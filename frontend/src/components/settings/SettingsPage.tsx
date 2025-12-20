import { useEffect, useState, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useTheme } from '@/hooks/useTheme'
import { aiApi } from '@/services/api'
import type { AiSettingsStatus } from '@/types'
import { KeyRound, Moon, Sun } from 'lucide-react'

export function SettingsPage() {
  const { theme, toggleTheme } = useTheme()
  const [apiKey, setApiKey] = useState('')
  const [status, setStatus] = useState<AiSettingsStatus | null>(null)
  const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash')
  const [originalModel, setOriginalModel] = useState('gemini-2.0-flash')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const result = await aiApi.getKeyStatus()
        setStatus(result)
        setSelectedModel(result.model)
        setOriginalModel(result.model)
        setAvailableModels(result.available_models || [])
      } catch (err) {
        console.error(err)
        setError('Failed to load AI settings.')
      } finally {
        setIsLoading(false)
      }
    }
    loadStatus()
  }, [])

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    if (!apiKey.trim()) {
      if (!status?.has_key && selectedModel !== originalModel) {
        setError('Save an API key before choosing a model.')
        return
      }
      if (selectedModel === originalModel) {
        setError('No changes to save.')
        return
      }
    }

    setIsSaving(true)
    try {
      const payload: { api_key?: string; model?: string } = {}
      if (apiKey.trim()) {
        payload.api_key = apiKey.trim()
      }
      if (selectedModel !== originalModel) {
        payload.model = selectedModel
      }
      const result = await aiApi.setKey(payload)
      setStatus(result)
      setApiKey('')
      setOriginalModel(result.model)
      setSelectedModel(result.model)
      setAvailableModels(result.available_models || [])
      setSuccess('Settings saved.')
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Failed to save API key.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    setError(null)
    setSuccess(null)
    setIsDeleting(true)
    try {
      const result = await aiApi.deleteKey()
      setStatus(result)
      setSuccess('Gemini API key removed.')
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Failed to remove API key.')
    } finally {
      setIsDeleting(false)
    }
  }

  const formatUpdatedAt = (value: string | null) => {
    if (!value) return 'Never'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return 'Unknown'
    return date.toLocaleString()
  }

  const modelLabels: Record<string, string> = {
    'gemini-2.0-flash': 'Gemini 2.0 Flash',
  }

  const showModelWarning = Boolean(
    status?.has_key && availableModels.length === 0
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage app preferences and AI integrations.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Appearance</CardTitle>
          <CardDescription>Adjust how the app looks for you.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium">Theme</p>
            <p className="text-xs text-muted-foreground">
              Switch between light and dark mode.
            </p>
          </div>
          <Button variant="outline" onClick={toggleTheme}>
            {theme === 'light' ? (
              <>
                <Moon className="mr-2 h-4 w-4" />
                Switch to dark
              </>
            ) : (
              <>
                <Sun className="mr-2 h-4 w-4" />
                Switch to light
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AI Response Recognition</CardTitle>
          <CardDescription>
            Store your Gemini API key to enable manual, per-thread AI classification.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-600">
              {success}
            </div>
          )}
          {showModelWarning && (
            <div className="mb-4 rounded-md border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm text-yellow-900">
              We could not load any models for this key. Try saving the key again.
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Badge variant="outline" className="bg-muted">
              Model: {modelLabels[selectedModel] || selectedModel}
            </Badge>
            <span className="text-muted-foreground">
              Status:{' '}
              {isLoading ? 'Loading...' : status?.has_key ? 'Key stored' : 'No key stored'}
            </span>
            <span className="text-muted-foreground">
              Updated: {isLoading ? '-' : formatUpdatedAt(status?.updated_at || null)}
            </span>
          </div>

          <form onSubmit={handleSave} className="mt-4 space-y-4">
            <div>
              <label className="text-sm font-medium">Model</label>
              <select
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value)}
                disabled={availableModels.length === 0}
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {availableModels.length === 0 && (
                  <option value={selectedModel}>Save a key to load models</option>
                )}
                {availableModels.map((model) => (
                  <option key={model} value={model}>
                    {modelLabels[model] || model}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Model list is fetched from Google when you save your API key.
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Gemini API key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="Paste your Gemini API key"
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Stored encrypted per user. Used only when you click AI Assist on a request.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={isSaving}>
                <KeyRound className="mr-2 h-4 w-4" />
                {isSaving ? 'Saving...' : 'Save Key'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleDelete}
                disabled={isDeleting || !status?.has_key}
              >
                {isDeleting ? 'Removing...' : 'Remove Key'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
