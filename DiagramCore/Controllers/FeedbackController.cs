using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using DiagramCore.Services.SelfLearning;
using DiagramCore.Models.Feedback;

namespace DiagramCore.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class FeedbackController : ControllerBase
    {
        private readonly IFeedbackService _feedbackService;
        private readonly LldQualityModel _qualityModel;

        public FeedbackController(IFeedbackService feedbackService, LldQualityModel qualityModel)
        {
            _feedbackService = feedbackService;
            _qualityModel = qualityModel;
        }

        [HttpPost("lld-quality")]
        public async Task<IActionResult> SubmitLldQualityFeedback([FromBody] LldQualityFeedback feedback)
        {
            await _feedbackService.StoreQualityFeedback(feedback);
            _qualityModel.RetrainIfNeeded();
            return Ok();
        }
    }
} 