import React, { useState } from 'react';
import { Rating } from '@mui/material';

interface QualityFeedbackProps {
  prediction: QualityPrediction;
  onFeedback: (feedback: UserQualityFeedback) => void;
}

const QualityFeedback: React.FC<QualityFeedbackProps> = ({ prediction, onFeedback }) => {
  const [detailedFeedback, setDetailedFeedback] = useState<Partial<UserQualityFeedback>>({});

  return (
    <div className="quality-feedback">
      <h3>Quality Assessment: {prediction.IsGoodQuality ? 'Good' : 'Needs Improvement'}</h3>
      <div className="feedback-section">
        <label>Layout Quality:</label>
        <Rating 
          value={detailedFeedback.layoutRating} 
          onChange={v => setDetailedFeedback({...detailedFeedback, layoutRating: v})}
        />
        
        <label>Labeling Quality:</label>
        <Rating
          value={detailedFeedback.labelingRating}
          onChange={v => setDetailedFeedback({...detailedFeedback, labelingRating: v})}
        />
        
        <button onClick={() => onFeedback(detailedFeedback as UserQualityFeedback)}>
          Submit Feedback
        </button>
      </div>
    </div>
  );
};

export default QualityFeedback; 