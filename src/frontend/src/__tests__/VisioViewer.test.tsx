import { render, screen } from '@testing-library/react';
import VisioViewer from '../components/VisioViewer';

const mockSVG = ['<svg><rect width="100" height="100"/></svg>'];

test('renders Visio viewer with controls', () => {
  render(<VisioViewer svgContents={mockSVG} />);
  
  expect(screen.getByText('Page 1')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '+' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Reset' })).toBeInTheDocument();
}); 