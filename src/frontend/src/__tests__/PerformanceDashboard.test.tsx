import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PerformanceDashboard } from '../components/PerformanceDashboard';
import { vi } from 'vitest';
import type { PerformanceData } from '../types/metrics';

describe('PerformanceDashboard', () => {
    const mockMetrics: PerformanceData = {
        deepseek: { 
            success_rate: 0.95, 
            avg_latency: 250,
            name: 'DeepSeek'
        }
    };

    beforeEach(() => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockMetrics
        });
    });

    it('renders metrics correctly', async () => {
        render(<PerformanceDashboard />);
        
        await waitFor(() => {
            expect(screen.getByText('95.0%')).toBeInTheDocument();
            expect(screen.getByText('250.00ms')).toBeInTheDocument();
        });
    });
}); 