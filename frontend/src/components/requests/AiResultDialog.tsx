import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { AiClassifyResult, DeletionRequest } from '@/types'
import { X, Sparkles } from 'lucide-react'

interface AiResultDialogProps {
  result: AiClassifyResult | null
  request: DeletionRequest | null
  brokerName?: string
  onClose: () => void
}

export function AiResultDialog({ result, request, brokerName, onClose }: AiResultDialogProps) {
  if (!result) return null

  const formatted = JSON.stringify(result.ai_output, null, 2)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />

      <Card className="relative z-10 w-full max-w-3xl mx-4 max-h-[85vh] overflow-hidden flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            AI Assist Output
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="overflow-y-auto flex-1 space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Badge variant="outline" className="bg-muted">
              Model: {result.model}
            </Badge>
            <Badge variant="outline" className="bg-muted">
              Updated: {result.updated_responses}
            </Badge>
            <Badge variant="outline" className="bg-muted">
              Status updated: {result.status_updated ? 'Yes' : 'No'}
            </Badge>
            <Badge variant="outline" className="bg-muted">
              Request status: {result.request_status}
            </Badge>
            {request && (
              <Badge variant="outline" className="bg-muted">
                Request: {brokerName || request.broker_id}
              </Badge>
            )}
          </div>

          <div className="rounded-lg border bg-muted/40 p-4">
            <p className="text-xs text-muted-foreground mb-2">
              Model output (JSON)
            </p>
            <pre className="text-xs whitespace-pre-wrap font-mono bg-background p-3 rounded-md border">
              {formatted}
            </pre>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
