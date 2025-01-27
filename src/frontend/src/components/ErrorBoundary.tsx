import React from 'react';
import { Box, Text, Button } from '@chakra-ui/react';

interface Props {
    children: React.ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
    state: State = { hasError: false };

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    render() {
        if (this.state.hasError) {
            return (
                <Box p={4} bg="red.50" borderRadius="md">
                    <Text color="red.500">Something went wrong!</Text>
                    <Button onClick={() => window.location.reload()}>
                        Retry
                    </Button>
                </Box>
            );
        }
        return this.props.children;
    }
} 