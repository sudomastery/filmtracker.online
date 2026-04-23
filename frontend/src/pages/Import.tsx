import { useState, useRef, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Upload, FileText, CheckCircle, XCircle, Loader2, Info } from 'lucide-react'
import { importService } from '@/services/user.service'
import { cn } from '@/utils/helpers'
import toast from 'react-hot-toast'

type ImportStatus = 'idle' | 'uploading' | 'processing' | 'done' | 'error'

interface ImportResult {
  line: string
  matched: boolean
  tmdb_id: number | null
  title: string | null
  poster_url: string | null
  release_year: number | null
  confidence: number | null
}

export default function ImportPage() {
  const [phase, setPhase] = useState<ImportStatus>('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Poll job status while processing
  const { data: statusData } = useQuery({
    queryKey: ['import-status', jobId],
    queryFn: () => importService.getStatus(jobId!).then(r => r.data),
    enabled: !!jobId && phase === 'processing',
    refetchInterval: (query) => {
      const d = query.state.data as any
      if (d?.status === 'done' || d?.status === 'error') return false
      return 1500
    },
  })

  // Fetch results when done
  const { data: resultsData } = useQuery({
    queryKey: ['import-results', jobId],
    queryFn: () => importService.getResults(jobId!).then(r => r.data),
    enabled: !!jobId && (phase === 'done' || statusData?.status === 'done'),
  })

  // Update phase from polled status
  if (statusData?.status === 'done' && phase === 'processing') {
    setPhase('done')
  }
  if (statusData?.status === 'error' && phase === 'processing') {
    setPhase('error')
  }

  const uploadMutation = useMutation({
    mutationFn: (file: File) => importService.uploadTxt(file),
    onSuccess: r => {
      setJobId(r.data.job_id)
      setPhase('processing')
    },
    onError: () => {
      setPhase('error')
      toast.error('Upload failed')
    },
  })

  const handleFile = useCallback((file: File) => {
    if (!file.name.endsWith('.txt')) {
      toast.error('Only .txt files are supported')
      return
    }
    setPhase('uploading')
    uploadMutation.mutate(file)
  }, [uploadMutation])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const results: ImportResult[] = resultsData?.results ?? []
  const matched = results.filter(r => r.matched).length
  const unmatched = results.filter(r => !r.matched).length

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3">
        <h1 className="text-lg font-bold text-white">Import Movies</h1>
      </div>

      <div className="px-4 py-6 space-y-6 max-w-lg">
        {/* Instructions */}
        <div className="flex gap-3 p-4 rounded-xl bg-surface-muted border border-surface-border">
          <Info className="w-5 h-5 text-brand-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1 text-sm text-gray-400">
            <p className="font-medium text-gray-300">How to import</p>
            <p>Upload a <code className="bg-surface-card px-1 rounded text-xs">.txt</code> file with one movie title per line.</p>
            <p>Optionally include a year: <code className="bg-surface-card px-1 rounded text-xs">Inception 2010</code></p>
          </div>
        </div>

        {/* Drop zone */}
        {phase === 'idle' || phase === 'error' ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={cn(
              'flex flex-col items-center justify-center gap-3 p-10 rounded-2xl border-2 border-dashed cursor-pointer transition-colors',
              dragOver
                ? 'border-brand-500 bg-brand-600/10'
                : 'border-surface-border hover:border-brand-600/50 hover:bg-surface-muted'
            )}
          >
            <Upload className="w-8 h-8 text-gray-500" />
            <div className="text-center">
              <p className="text-gray-300 font-medium">Drop your file here</p>
              <p className="text-gray-500 text-sm mt-1">or click to browse</p>
            </div>
            <p className="text-xs text-gray-600">.txt files only</p>

            {phase === 'error' && (
              <p className="text-red-400 text-xs mt-1">Upload failed. Try again.</p>
            )}
          </div>
        ) : null}

        <input
          ref={fileInputRef}
          type="file"
          accept=".txt"
          className="hidden"
          onChange={e => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />

        {/* Uploading */}
        {phase === 'uploading' && (
          <div className="flex flex-col items-center gap-3 py-10">
            <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
            <p className="text-gray-400 text-sm">Uploading file…</p>
          </div>
        )}

        {/* Processing */}
        {phase === 'processing' && (
          <div className="flex flex-col items-center gap-3 py-10">
            <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
            <p className="text-gray-300 font-medium">Matching movies…</p>
            {statusData?.total > 0 && (
              <div className="w-full max-w-xs bg-surface-muted rounded-full h-2">
                <div
                  className="bg-brand-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.round((statusData.processed / statusData.total) * 100)}%` }}
                />
              </div>
            )}
            <p className="text-gray-600 text-xs">This may take a moment</p>
          </div>
        )}

        {/* Results */}
        {(phase === 'done' || (statusData?.status === 'done' && results.length > 0)) && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="flex gap-3">
              <div className="flex-1 p-3 rounded-xl bg-green-500/10 border border-green-500/20 text-center">
                <p className="text-2xl font-bold text-green-400">{matched}</p>
                <p className="text-xs text-gray-400 mt-0.5">Matched</p>
              </div>
              <div className="flex-1 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                <p className="text-2xl font-bold text-red-400">{unmatched}</p>
                <p className="text-xs text-gray-400 mt-0.5">Unmatched</p>
              </div>
              <div className="flex-1 p-3 rounded-xl bg-surface-muted border border-surface-border text-center">
                <p className="text-2xl font-bold text-white">{results.length}</p>
                <p className="text-xs text-gray-400 mt-0.5">Total</p>
              </div>
            </div>

            {/* Import another */}
            <button
              onClick={() => { setPhase('idle'); setJobId(null) }}
              className="w-full py-2.5 rounded-xl border border-surface-border text-sm text-gray-300 hover:bg-surface-muted transition-colors"
            >
              Import another file
            </button>

            {/* Result list */}
            <div className="space-y-2">
              {results.map((r, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-xl border',
                    r.matched
                      ? 'border-green-500/20 bg-green-500/5'
                      : 'border-red-500/20 bg-red-500/5'
                  )}
                >
                  {r.matched && r.poster_url ? (
                    <img
                      src={r.poster_url}
                      alt={r.title ?? ''}
                      className="w-8 h-12 rounded-md object-cover flex-shrink-0 bg-surface-border"
                      onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
                    />
                  ) : (
                    <div className="w-8 h-12 rounded-md bg-surface-muted flex-shrink-0 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-gray-600" />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {r.title ?? r.line}
                    </p>
                    {r.release_year && (
                      <p className="text-xs text-gray-500">{r.release_year}</p>
                    )}
                    {!r.matched && (
                      <p className="text-xs text-gray-500">"{r.line}" — not found</p>
                    )}
                  </div>

                  {r.matched ? (
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
