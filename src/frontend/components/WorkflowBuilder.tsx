import React, { useState, useCallback } from 'react';
import ReactFlow, { 
    Controls, 
    Panel, 
    Edge, 
    Connection, 
    addEdge,
    Node,
    NodeChange,
    applyNodeChanges
} from 'reactflow';
import { Button } from '@chakra-ui/react';
import 'reactflow/dist/style.css';

interface WorkflowNode extends Node {
    type: 'componentExtractor' | 'specsFetcher' | 'diagramGenerator';
    data: {
        label: string;
        inputs: string[];
        outputs: string[];
    };
}

const WorkflowCanvas: React.FC = () => {
    const [nodes, setNodes] = useState<WorkflowNode[]>([
        {
            id: '1',
            type: 'componentExtractor',
            position: { x: 0, y: 0 },
            data: {
                label: 'Component Extractor',
                inputs: ['text'],
                outputs: ['components']
            }
        }
    ]);
    const [edges, setEdges] = useState<Edge[]>([]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        []
    );

    const onNodesChange = useCallback(
        (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
        []
    );

    const deployWorkflow = async () => {
        try {
            const response = await fetch('/api/execute-workflow', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nodes, edges })
            });
            const result = await response.json();
            console.log('Workflow deployed:', result);
        } catch (error) {
            console.error('Workflow deployment failed:', error);
        }
    };

    return (
        <div style={{ width: '100%', height: '100vh' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onConnect={onConnect}
                fitView
            >
                <Controls />
                <Panel position="top-right">
                    <Button onClick={deployWorkflow}>
                        Deploy Workflow
                    </Button>
                </Panel>
            </ReactFlow>
        </div>
    );
};

export default WorkflowCanvas; 