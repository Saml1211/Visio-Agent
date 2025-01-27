import { useState } from 'react';
import { Switch, Slider, Input, Box, Heading, Button } from '@chakra-ui/react';

interface ModelConfig {
  enabled: boolean;
  apiKey: string;
  temperature: number;
  maxTokens: number;
}

export const ModelSettings = () => {
  const [models, setModels] = useState({
    deepseek: { enabled: true, apiKey: '', temperature: 0.7, maxTokens: 1000 },
    gemini: { enabled: false, apiKey: '', temperature: 0.5, maxTokens: 800 },
    openai: { enabled: false, apiKey: '', temperature: 0.4, maxTokens: 1200 }
  });

  const updateModelConfig = (model: keyof typeof models, field: string, value: any) => {
    setModels(prev => ({
      ...prev,
      [model]: { ...prev[model], [field]: value }
    }));
  };

  const saveConfiguration = async () => {
    try {
      const response = await fetch('/api/update-config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(models)
      });
      
      if (!response.ok) throw new Error('Save failed');
      // Update UI state
    } catch (err) {
      // Handle error
    }
  }

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg">
      <Heading size="md" mb={4}>AI Model Configuration</Heading>
      
      {Object.entries(models).map(([key, config]) => (
        <Box key={key} mb={4} p={4} bg="gray.50" borderRadius="md">
          <Switch
            isChecked={config.enabled}
            onChange={(e) => updateModelConfig(key, 'enabled', e.target.checked)}
            mr={2}
          >
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </Switch>
          
          {config.enabled && (
            <Box mt={2} pl={6}>
              <Input
                type="password"
                placeholder={`${key} API Key`}
                value={config.apiKey}
                onChange={(e) => updateModelConfig(key, 'apiKey', e.target.value)}
                mb={2}
              />
              
              <Box mb={2}>
                <label>Temperature ({config.temperature})</label>
                <Slider
                  min={0} max={1} step={0.1}
                  value={config.temperature}
                  onChange={(v) => updateModelConfig(key, 'temperature', v)}
                />
              </Box>
              
              <Box>
                <label>Max Tokens ({config.maxTokens})</label>
                <Slider
                  min={100} max={2000} step={100}
                  value={config.maxTokens}
                  onChange={(v) => updateModelConfig(key, 'maxTokens', v)}
                />
              </Box>
            </Box>
          )}
        </Box>
      ))}
      <Button onClick={saveConfiguration} colorScheme="blue" mt={4}>
        Save Configuration
      </Button>
    </Box>
  );
}; 