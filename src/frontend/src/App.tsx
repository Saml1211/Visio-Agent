import React, { useState, useEffect, useCallback } from 'react';
import {
  ChakraProvider,
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Button,
  Input,
  Select,
  Progress,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  FormControl,
  FormLabel,
  Textarea,
  Code,
  Link,
  Divider,
  Grid,
  GridItem
} from '@chakra-ui/react';
import { FiUpload, FiDownload, FiSettings, FiRefreshCw } from 'react-icons/fi';
import axios from 'axios';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary'

// API client
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000'
});

interface Template {
  name: string;
  description: string;
}

interface WorkflowStep {
  name: string;
  status: string;
  start_time?: string;
  end_time?: string;
  error?: string;
  metadata?: any;
}

interface WorkflowStatus {
  workflow_id: string;
  status: string;
  steps: WorkflowStep[];
}

interface AIConfig {
  providers: string[];
  models: Record<string, string[]>;
  current_config: Record<string, any>;
}

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert">
      <h2>Application Error</h2>
      <pre>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try Again</button>
    </div>
  );
}

function App() {
  // State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [processing, setProcessing] = useState(false);
  const [currentWorkflow, setCurrentWorkflow] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [aiConfig, setAIConfig] = useState<AIConfig | null>(null);
  const [feedback, setFeedback] = useState({
    type: '',
    text: '',
    confidence: 0.5
  });
  const [visioData, setVisioData] = useState(null);
  
  const toast = useToast();
  
  // Load templates and AI config on mount
  useEffect(() => {
    loadTemplates();
    loadAIConfig();
  }, []);
  
  // Poll workflow status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (currentWorkflow && processing) {
      interval = setInterval(checkWorkflowStatus, 2000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [currentWorkflow, processing]);
  
  // Load templates
  const loadTemplates = async () => {
    try {
      const response = await api.get('/api/templates');
      setTemplates(response.data);
    } catch (error) {
      toast({
        title: 'Error loading templates',
        status: 'error',
        duration: 5000
      });
    }
  };
  
  // Load AI config
  const loadAIConfig = async () => {
    try {
      const response = await api.get('/api/config/ai');
      setAIConfig(response.data);
    } catch (error) {
      toast({
        title: 'Error loading AI configuration',
        status: 'error',
        duration: 5000
      });
    }
  };
  
  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };
  
  // Handle file upload and processing
  const handleUploadAndProcess = async () => {
    if (!selectedFile || !selectedTemplate) {
      toast({
        title: 'Please select a file and template',
        status: 'warning',
        duration: 5000
      });
      return;
    }
    
    try {
      setProcessing(true);
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      const uploadResponse = await api.post('/api/upload', formData);
      
      const processResponse = await api.post('/api/process', {
        file_path: uploadResponse.data.file_path,
        template_name: selectedTemplate
      });
      
      setCurrentWorkflow(processResponse.data.workflow_id);
      
      toast({
        title: 'Processing started',
        status: 'success',
        duration: 5000
      });
      
    } catch (error) {
      toast({
        title: 'Error processing document',
        status: 'error',
        duration: 5000
      });
      setProcessing(false);
    }
  };
  
  // Check workflow status
  const checkWorkflowStatus = async () => {
    if (!currentWorkflow) return;
    
    try {
      const response = await api.get(`/api/status/${currentWorkflow}`);
      setWorkflowStatus(response.data);
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        setProcessing(false);
      }
      
    } catch (error) {
      console.error('Error checking workflow status:', error);
    }
  };
  
  // Download files
  const handleDownload = async (type: 'visio' | 'pdf') => {
    if (!currentWorkflow) return;
    
    try {
      const response = await api.get(
        `/api/download/${currentWorkflow}/${type}`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${currentWorkflow}.${type === 'visio' ? 'vsdx' : 'pdf'}`;
      link.click();
      
    } catch (error) {
      toast({
        title: `Error downloading ${type} file`,
        status: 'error',
        duration: 5000
      });
    }
  };
  
  // Submit feedback
  const handleFeedbackSubmit = async () => {
    if (!currentWorkflow) return;
    
    try {
      await api.post('/api/feedback', {
        workflow_id: currentWorkflow,
        feedback_type: feedback.type,
        input_data: selectedFile?.name,
        expected_output: 'Expected output',
        actual_output: 'Actual output',
        user_feedback: feedback.text,
        confidence_score: feedback.confidence
      });
      
      toast({
        title: 'Feedback submitted',
        status: 'success',
        duration: 5000
      });
      
      setFeedback({
        type: '',
        text: '',
        confidence: 0.5
      });
      
    } catch (error) {
      toast({
        title: 'Error submitting feedback',
        status: 'error',
        duration: 5000
      });
    }
  };
  
  // Update AI config
  const handleConfigUpdate = async (config: Record<string, any>) => {
    try {
      await api.post('/api/config/ai', config);
      await loadAIConfig();
      
      toast({
        title: 'Configuration updated',
        status: 'success',
        duration: 5000
      });
      
    } catch (error) {
      toast({
        title: 'Error updating configuration',
        status: 'error',
        duration: 5000
      });
    }
  };
  
  const loadDiagram = useCallback(async (id: string) => {
    try {
      const response = await fetch(`/api/diagrams/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setVisioData(data);
    } catch (error) {
      console.error('Diagram load failed:', error);
      throw new Error('Failed to load diagram data');
    }
  }, []);
  
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <ChakraProvider>
        <Container maxW="container.xl" py={8}>
          <VStack spacing={8} align="stretch">
            <Heading>LLD Automation System</Heading>
            
            <Tabs>
              <TabList>
                <Tab>Process Document</Tab>
                <Tab>Status</Tab>
                <Tab>Configuration</Tab>
              </TabList>
              
              <TabPanels>
                {/* Process Document Tab */}
                <TabPanel>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel>Upload Document</FormLabel>
                      <Input
                        type="file"
                        onChange={handleFileSelect}
                        accept=".pdf,.docx,.txt,.csv"
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel>Select Template</FormLabel>
                      <Select
                        value={selectedTemplate}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                      >
                        <option value="">Select a template</option>
                        {templates.map((template) => (
                          <option key={template.name} value={template.name}>
                            {template.name}
                          </option>
                        ))}
                      </Select>
                    </FormControl>
                    
                    <Button
                      leftIcon={<FiUpload />}
                      colorScheme="blue"
                      onClick={handleUploadAndProcess}
                      isLoading={processing}
                      loadingText="Processing..."
                    >
                      Upload & Process
                    </Button>
                  </VStack>
                </TabPanel>
                
                {/* Status Tab */}
                <TabPanel>
                  {workflowStatus && (
                    <VStack spacing={4} align="stretch">
                      <Text>
                        Workflow ID: <Code>{workflowStatus.workflow_id}</Code>
                      </Text>
                      <Text>
                        Status: <Code>{workflowStatus.status}</Code>
                      </Text>
                      
                      <Box>
                        <Text fontWeight="bold" mb={2}>Steps:</Text>
                        {workflowStatus.steps.map((step, index) => (
                          <Box
                            key={index}
                            p={4}
                            borderWidth={1}
                            borderRadius="md"
                            mb={2}
                          >
                            <Text>Name: {step.name}</Text>
                            <Text>Status: {step.status}</Text>
                            {step.error && (
                              <Text color="red.500">Error: {step.error}</Text>
                            )}
                            {step.metadata && (
                              <Text>
                                Metadata: <Code>{JSON.stringify(step.metadata)}</Code>
                              </Text>
                            )}
                          </Box>
                        ))}
                      </Box>
                      
                      {workflowStatus.status === 'completed' && (
                        <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                          <Button
                            leftIcon={<FiDownload />}
                            onClick={() => handleDownload('visio')}
                          >
                            Download Visio
                          </Button>
                          <Button
                            leftIcon={<FiDownload />}
                            onClick={() => handleDownload('pdf')}
                          >
                            Download PDF
                          </Button>
                        </Grid>
                      )}
                      
                      <Divider my={4} />
                      
                      <Box>
                        <Text fontWeight="bold" mb={2}>Provide Feedback:</Text>
                        <VStack spacing={4}>
                          <FormControl>
                            <FormLabel>Feedback Type</FormLabel>
                            <Select
                              value={feedback.type}
                              onChange={(e) => setFeedback({
                                ...feedback,
                                type: e.target.value
                              })}
                            >
                              <option value="">Select type</option>
                              <option value="data_refinement">Data Refinement</option>
                              <option value="component_extraction">Component Extraction</option>
                              <option value="layout_generation">Layout Generation</option>
                            </Select>
                          </FormControl>
                          
                          <FormControl>
                            <FormLabel>Feedback Text</FormLabel>
                            <Textarea
                              value={feedback.text}
                              onChange={(e) => setFeedback({
                                ...feedback,
                                text: e.target.value
                              })}
                            />
                          </FormControl>
                          
                          <FormControl>
                            <FormLabel>Confidence Score</FormLabel>
                            <Input
                              type="number"
                              min={0}
                              max={1}
                              step={0.1}
                              value={feedback.confidence}
                              onChange={(e) => setFeedback({
                                ...feedback,
                                confidence: parseFloat(e.target.value)
                              })}
                            />
                          </FormControl>
                          
                          <Button
                            colorScheme="blue"
                            onClick={handleFeedbackSubmit}
                          >
                            Submit Feedback
                          </Button>
                        </VStack>
                      </Box>
                    </VStack>
                  )}
                </TabPanel>
                
                {/* Configuration Tab */}
                <TabPanel>
                  {aiConfig && (
                    <VStack spacing={4} align="stretch">
                      <Text fontWeight="bold">AI Service Configuration</Text>
                      
                      <FormControl>
                        <FormLabel>Default Provider</FormLabel>
                        <Select
                          value={aiConfig.current_config.default_provider}
                          onChange={(e) => handleConfigUpdate({
                            ...aiConfig.current_config,
                            default_provider: e.target.value
                          })}
                        >
                          {aiConfig.providers.map((provider) => (
                            <option key={provider} value={provider}>
                              {provider}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                      
                      {Object.entries(aiConfig.models).map(([provider, models]) => (
                        <FormControl key={provider}>
                          <FormLabel>{provider} Model</FormLabel>
                          <Select
                            value={aiConfig.current_config[`${provider}_model`]}
                            onChange={(e) => handleConfigUpdate({
                              ...aiConfig.current_config,
                              [`${provider}_model`]: e.target.value
                            })}
                          >
                            {models.map((model) => (
                              <option key={model} value={model}>
                                {model}
                              </option>
                            ))}
                          </Select>
                        </FormControl>
                      ))}
                      
                      <Button
                        leftIcon={<FiRefreshCw />}
                        onClick={loadAIConfig}
                      >
                        Refresh Configuration
                      </Button>
                    </VStack>
                  )}
                </TabPanel>
              </TabPanels>
            </Tabs>
          </VStack>
        </Container>
      </ChakraProvider>
    </ErrorBoundary>
  );
}

export default App; 