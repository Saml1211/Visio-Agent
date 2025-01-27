import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { cleanup } from '@testing-library/react';

beforeEach(() => {
    // Initialize test environment
    global.fetch = vi.fn();
});

afterEach(() => {
    cleanup();
    vi.clearAllMocks();
}); 