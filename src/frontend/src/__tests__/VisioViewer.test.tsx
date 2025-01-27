import { render, screen } from '@testing-library/react';
import VisioViewer from '../components/VisioViewer';
import type { VisioData } from '../types/visio';

const mockVisioData: VisioData = {
  pages: [{
    svg: '<svg><rect width="100" height="100"/></svg>',
    pageNumber: 1,
    shapes: []
  }],
  metadata: { width: 1000, height: 800 }
};

describe('VisioViewer Component', () => {
  test('renders empty container when no data', () => {
    render(<VisioViewer data={null} />);
    const container = screen.getByTestId('visio-container');
    expect(container).toBeEmptyDOMElement();
  });

  test('throws error with invalid data structure', () => {
    const invalidData = { invalid: true } as unknown as VisioData;
    expect(() => render(<VisioViewer data={invalidData} />))
      .toThrow('Failed to initialize Visio viewer');
  });

  test('handles cleanup on unmount', () => {
    const { unmount } = render(<VisioViewer data={mockVisioData} />);
    expect(() => unmount()).not.toThrow();
  });
}); 