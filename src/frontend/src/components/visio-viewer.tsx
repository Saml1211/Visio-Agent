'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'

export function VisioViewer() {
  const { toast } = useToast()
  const [diagram, setDiagram] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDiagram()
  }, [])

  const fetchDiagram = async () => {
    try {
      const response = await fetch('/api/diagrams/latest')
      if (!response.ok) {
        throw new Error('Failed to fetch diagram')
      }
      const data = await response.json()
      setDiagram(data.data.svgContent)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load diagram',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>
  }

  if (!diagram) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <p className="text-muted-foreground">No diagram available</p>
        <Button onClick={fetchDiagram}>Refresh</Button>
      </div>
    )
  }

  return (
    <div className="w-full h-full overflow-auto">
      <div 
        className="w-full h-full"
        dangerouslySetInnerHTML={{ __html: diagram }}
      />
    </div>
  )
} 