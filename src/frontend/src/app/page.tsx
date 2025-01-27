import { WorkflowBuilder } from '@/components/workflow-builder'
import { VisioViewer } from '@/components/visio-viewer'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'

export default function Home() {
  const { toast } = useToast()
  
  return (
    <div className="min-h-screen bg-muted/40">
      <header className="bg-background border-b">
        <div className="container flex h-14 items-center px-4">
          <h1 className="text-lg font-semibold">Visio Agent</h1>
        </div>
      </header>

      <main className="container grid flex-1 gap-4 p-4 md:grid-cols-2">
        <Card className="h-[calc(100vh-9rem)]">
          <CardHeader>
            <CardTitle>Workflow Builder</CardTitle>
          </CardHeader>
          <CardContent>
            <WorkflowBuilder />
          </CardContent>
        </Card>

        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Document Upload</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="grid w-full items-center gap-1.5">
                  <Label htmlFor="document">Upload Technical Document</Label>
                  <Input id="document" type="file" />
                </div>
                <Button className="w-full">Process Document</Button>
              </div>
            </CardContent>
          </Card>

          <Card className="h-[500px]">
            <CardHeader>
              <CardTitle>Diagram Preview</CardTitle>
            </CardHeader>
            <CardContent className="h-full">
              <VisioViewer />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
} 