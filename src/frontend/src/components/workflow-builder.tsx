'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'

export function WorkflowBuilder() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [workflow, setWorkflow] = useState({
    name: '',
    description: '',
    steps: []
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch('/api/workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflow),
      })

      if (!response.ok) {
        throw new Error('Failed to create workflow')
      }

      toast({
        title: 'Success',
        description: 'Workflow created successfully',
      })

      // Reset form
      setWorkflow({
        name: '',
        description: '',
        steps: []
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create workflow',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Workflow Name</Label>
        <Input
          id="name"
          value={workflow.name}
          onChange={(e) => setWorkflow({ ...workflow, name: e.target.value })}
          placeholder="Enter workflow name"
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={workflow.description}
          onChange={(e) => setWorkflow({ ...workflow, description: e.target.value })}
          placeholder="Enter workflow description"
          required
        />
      </div>
      <Button type="submit" disabled={loading}>
        {loading ? 'Creating...' : 'Create Workflow'}
      </Button>
    </form>
  )
} 