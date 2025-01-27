interface QualityPrediction {
    IsGoodQuality: boolean;
    Probability: number;
}

interface UserQualityFeedback {
    layoutRating: number;
    labelingRating: number;
    comments?: string;
} 