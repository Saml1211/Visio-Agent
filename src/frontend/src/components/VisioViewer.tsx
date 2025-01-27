import React, { useState } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

interface VisioViewerProps {
  svgContents: string[];
}

const VisioViewer: React.FC<VisioViewerProps> = ({ svgContents }) => {
  const [currentPage, setCurrentPage] = useState(0);

  return (
    <div className="visio-viewer">
      <div className="page-controls">
        {svgContents.map((_, idx) => (
          <button 
            key={idx}
            onClick={() => setCurrentPage(idx)}
            className={idx === currentPage ? 'active' : ''}
          >
            Page {idx + 1}
          </button>
        ))}
      </div>
      
      <TransformWrapper>
        {({ zoomIn, zoomOut, resetTransform }) => (
          <>
            <div className="zoom-controls">
              <button onClick={() => zoomIn()}>+</button>
              <button onClick={() => zoomOut()}>-</button>
              <button onClick={() => resetTransform()}>Reset</button>
            </div>
            
            <TransformComponent>
              <div 
                dangerouslySetInnerHTML={{ __html: svgContents[currentPage] }} 
                className="svg-container"
              />
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
};

export default VisioViewer; 