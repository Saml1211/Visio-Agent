import React, { useRef, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import VisioViewerCore from '../core/VisioViewerCore';
import type { VisioData } from '../types/visio';

interface VisioViewerProps {
  data: VisioData | null;
}

function VisioViewer({ data }: VisioViewerProps) {
  const visioRef = useRef<HTMLDivElement>(null);
  const viewerInstance = useRef<VisioViewerCore | null>(null);

  useEffect(() => {
    if (!data || !visioRef.current) return;

    try {
      viewerInstance.current = new VisioViewerCore({
        container: visioRef.current,
        data,
        onError: (err: Error) => {
          console.error('Visio rendering error:', err);
          throw new Error(`Diagram rendering failed: ${err.message}`);
        }
      });

      return () => {
        viewerInstance.current?.cleanup();
        viewerInstance.current = null;
      };
    } catch (error) {
      console.error('Visio initialization failed:', error);
      throw new Error('Failed to initialize Visio viewer');
    }
  }, [data]);

  return (
    <div ref={visioRef} className="visio-container" data-testid="visio-container" />
  );
}

export default VisioViewer; 