import { useEffect, useState } from 'react';
import { Box, Heading, SimpleGrid, Stat, StatLabel, StatNumber } from '@chakra-ui/react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { PerformanceData } from '../types/metrics';

export const PerformanceDashboard = () => {
    const [metrics, setMetrics] = useState<PerformanceData>({});

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await fetch('/api/performance-metrics');
                if (!response.ok) throw new Error('Failed to fetch metrics');
                const data = await response.json();
                setMetrics(data);
            } catch (error) {
                console.error('Error fetching metrics:', error);
            }
        };

        fetchMetrics();
        const interval = setInterval(fetchMetrics, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <Box p={4}>
            <Heading mb={4}>Model Performance</Heading>
            <SimpleGrid columns={3} spacing={4} mb={8}>
                {Object.entries(metrics).map(([model, data]) => (
                    <Box key={model} p={4} bg="white" borderRadius="md" boxShadow="md">
                        <Heading size="sm" mb={2}>{model.toUpperCase()}</Heading>
                        <Stat>
                            <StatLabel>Success Rate</StatLabel>
                            <StatNumber>{(data.success_rate * 100).toFixed(1)}%</StatNumber>
                        </Stat>
                        <Stat mt={2}>
                            <StatLabel>Avg Latency</StatLabel>
                            <StatNumber>{data.avg_latency.toFixed(2)}ms</StatNumber>
                        </Stat>
                    </Box>
                ))}
            </SimpleGrid>
            
            <Box bg="white" p={4} borderRadius="md" boxShadow="md">
                <Heading size="sm" mb={4}>Latency Trends</Heading>
                <LineChart width={800} height={300} data={Object.values(metrics)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="avg_latency" stroke="#8884d8" />
                </LineChart>
            </Box>
        </Box>
    );
}; 