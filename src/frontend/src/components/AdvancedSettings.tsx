import { useState } from 'react';
import {
    Box,
    Switch,
    FormControl,
    FormLabel,
    Input,
    VStack,
    Heading,
    useToast,
} from '@chakra-ui/react';

export const AdvancedSettings = () => {
    const toast = useToast();
    const [settings, setSettings] = useState({
        enableWebCrawling: false,
        showAlternatives: true,
        firecrawlKey: '',
    });

    const handleChange = (field: string) => (value: any) => {
        try {
            setSettings(prev => ({
                ...prev,
                [field]: value
            }));
        } catch (error) {
            toast({
                title: "Error updating settings",
                description: error.message,
                status: "error",
                duration: 5000,
            });
        }
    };

    return (
        <Box p={4} borderWidth="1px" borderRadius="lg">
            <Heading size="md" mb={4}>Advanced Settings</Heading>
            
            <VStack spacing={4} align="stretch">
                <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">
                        Enable Web Crawling
                    </FormLabel>
                    <Switch
                        isChecked={settings.enableWebCrawling}
                        onChange={(e) => handleChange('enableWebCrawling')(e.target.checked)}
                    />
                </FormControl>

                <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">
                        Show Alternative Components
                    </FormLabel>
                    <Switch
                        isChecked={settings.showAlternatives}
                        onChange={(e) => handleChange('showAlternatives')(e.target.checked)}
                    />
                </FormControl>

                <FormControl>
                    <FormLabel>Firecrawl API Key</FormLabel>
                    <Input
                        type="password"
                        value={settings.firecrawlKey}
                        onChange={(e) => handleChange('firecrawlKey')(e.target.value)}
                        placeholder="Enter API key"
                    />
                </FormControl>
            </VStack>
        </Box>
    );
}; 