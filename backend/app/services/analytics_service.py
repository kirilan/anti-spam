"""
Analytics Service
Provides statistical analysis and insights about deletion requests and broker responses
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.broker_response import BrokerResponse, ResponseType
from app.models.data_broker import DataBroker


class AnalyticsService:
    """Service for generating analytics and statistics"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_stats(self, user_id: str) -> Dict:
        """
        Get overall statistics for a user

        Returns:
            Dict with total_requests, confirmed, sent, rejected, pending,
            success_rate, average_response_time_days
        """
        # Count requests by status
        status_counts = (
            self.db.query(
                DeletionRequest.status,
                func.count(DeletionRequest.id).label('count')
            )
            .filter(DeletionRequest.user_id == user_id)
            .group_by(DeletionRequest.status)
            .all()
        )

        # Convert to dict
        stats = {
            'total_requests': 0,
            'confirmed_deletions': 0,
            'sent_requests': 0,
            'rejected': 0,
            'pending_requests': 0
        }

        for status, count in status_counts:
            stats['total_requests'] += count
            if status == RequestStatus.CONFIRMED:
                stats['confirmed_deletions'] = count
            elif status == RequestStatus.SENT:
                stats['sent_requests'] = count
            elif status == RequestStatus.REJECTED:
                stats['rejected'] = count
            elif status == RequestStatus.PENDING:
                stats['pending_requests'] = count

        # Calculate success rate
        total_sent = stats['confirmed_deletions'] + stats['sent_requests'] + stats['rejected']
        if total_sent > 0:
            stats['success_rate'] = round((stats['confirmed_deletions'] / total_sent) * 100, 1)
        else:
            stats['success_rate'] = 0.0

        # Calculate average response time
        confirmed_requests = (
            self.db.query(DeletionRequest)
            .filter(
                DeletionRequest.user_id == user_id,
                DeletionRequest.status == RequestStatus.CONFIRMED,
                DeletionRequest.sent_at.isnot(None),
                DeletionRequest.confirmed_at.isnot(None)
            )
            .all()
        )

        if confirmed_requests:
            total_days = sum(
                (req.confirmed_at - req.sent_at).days
                for req in confirmed_requests
            )
            stats['avg_response_time_days'] = round(total_days / len(confirmed_requests), 1)
        else:
            stats['avg_response_time_days'] = None

        return stats

    def get_broker_compliance_ranking(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Get broker compliance ranking

        Args:
            user_id: Optional user ID to filter by specific user's requests

        Returns:
            List of dicts with broker_id, broker_name, total_requests,
            confirmed, rejected, success_rate, average_response_days
            Sorted by success_rate descending
        """
        query = self.db.query(
            DataBroker.id.label('broker_id'),
            DataBroker.name.label('broker_name'),
            func.count(DeletionRequest.id).label('total_requests'),
            func.sum(
                case((DeletionRequest.status == RequestStatus.CONFIRMED, 1), else_=0)
            ).label('confirmed'),
            func.sum(
                case((DeletionRequest.status == RequestStatus.REJECTED, 1), else_=0)
            ).label('rejected')
        ).join(
            DeletionRequest,
            DeletionRequest.broker_id == DataBroker.id
        )

        if user_id:
            query = query.filter(DeletionRequest.user_id == user_id)

        results = query.group_by(
            DataBroker.id,
            DataBroker.name
        ).all()

        # Calculate success rates and average response times
        rankings = []
        for row in results:
            total_completed = row.confirmed + row.rejected
            success_rate = (row.confirmed / total_completed * 100) if total_completed > 0 else 0

            # Get average response time for this broker
            confirmed_requests = (
                self.db.query(DeletionRequest)
                .filter(
                    DeletionRequest.broker_id == row.broker_id,
                    DeletionRequest.status == RequestStatus.CONFIRMED,
                    DeletionRequest.sent_at.isnot(None),
                    DeletionRequest.confirmed_at.isnot(None)
                )
            )

            if user_id:
                confirmed_requests = confirmed_requests.filter(
                    DeletionRequest.user_id == user_id
                )

            confirmed_requests = confirmed_requests.all()

            if confirmed_requests:
                total_days = sum(
                    (req.confirmed_at - req.sent_at).days
                    for req in confirmed_requests
                )
                avg_response_days = round(total_days / len(confirmed_requests), 1)
            else:
                avg_response_days = 0.0

            rankings.append({
                'broker_id': str(row.broker_id),
                'broker_name': row.broker_name,
                'total_requests': row.total_requests,
                'confirmations': row.confirmed,
                'rejected': row.rejected,
                'success_rate': round(success_rate, 1),
                'avg_response_time_days': avg_response_days if avg_response_days > 0 else None
            })

        # Sort by success rate descending, then by total requests
        rankings.sort(key=lambda x: (-x['success_rate'], -x['total_requests']))

        return rankings

    def get_timeline_data(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Get timeline data for requests sent and confirmations received

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of dicts with date, requests_sent, confirmations_received
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get requests sent per day
        sent_by_day = (
            self.db.query(
                func.date(DeletionRequest.sent_at).label('date'),
                func.count(DeletionRequest.id).label('count')
            )
            .filter(
                DeletionRequest.user_id == user_id,
                DeletionRequest.sent_at >= cutoff_date,
                DeletionRequest.sent_at.isnot(None)
            )
            .group_by(func.date(DeletionRequest.sent_at))
            .all()
        )

        # Get confirmations received per day
        confirmed_by_day = (
            self.db.query(
                func.date(DeletionRequest.confirmed_at).label('date'),
                func.count(DeletionRequest.id).label('count')
            )
            .filter(
                DeletionRequest.user_id == user_id,
                DeletionRequest.confirmed_at >= cutoff_date,
                DeletionRequest.confirmed_at.isnot(None)
            )
            .group_by(func.date(DeletionRequest.confirmed_at))
            .all()
        )

        # Merge data by date
        timeline = {}

        for row in sent_by_day:
            date_str = row.date.isoformat()
            timeline[date_str] = {
                'date': date_str,
                'requests_sent': row.count,
                'confirmations_received': 0
            }

        for row in confirmed_by_day:
            date_str = row.date.isoformat()
            if date_str in timeline:
                timeline[date_str]['confirmations_received'] = row.count
            else:
                timeline[date_str] = {
                    'date': date_str,
                    'requests_sent': 0,
                    'confirmations_received': row.count
                }

        # Convert to sorted list
        result = sorted(timeline.values(), key=lambda x: x['date'])

        return result

    def get_response_type_distribution(self, user_id: str) -> List[Dict]:
        """
        Get distribution of response types

        Args:
            user_id: User ID

        Returns:
            List of dicts with response_type, count, and percentage
        """
        results = (
            self.db.query(
                BrokerResponse.response_type,
                func.count(BrokerResponse.id).label('count')
            )
            .filter(BrokerResponse.user_id == user_id)
            .group_by(BrokerResponse.response_type)
            .all()
        )

        # Calculate total for percentage
        total = sum(row.count for row in results)

        # Avoid division by zero
        if total == 0:
            return []

        return [
            {
                'response_type': row.response_type.value,
                'count': row.count,
                'percentage': round((row.count / total) * 100, 1)
            }
            for row in results
        ]
