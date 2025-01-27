export enum WorkflowStatus {
    PENDING = 'pending',
    RUNNING = 'running',
    COMPLETED = 'completed',
    FAILED = 'failed'
}

export enum WorkflowStepType {
    DATA_REFINEMENT = 'data_refinement',
    COMPONENT_EXTRACTION = 'component_extraction',
    VISIO_GENERATION = 'visio_generation'
}

export interface WorkflowMetadata {
    created_at: string;
    step_count: number;
    failed_steps: number;
    [key: string]: unknown;
}

export interface WorkflowStep {
    name: WorkflowStepType;
    status: WorkflowStatus;
    start_time?: string;
    end_time?: string;
    error?: string;
    metadata?: WorkflowMetadata;
}

export interface WorkflowResult {
    workflow_id: string;
    status: WorkflowStatus;
    steps: WorkflowStep[];
    visio_file_path?: string;
    pdf_file_path?: string;
} 