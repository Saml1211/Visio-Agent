using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using System.Threading.Tasks;
using DiagramCore.Services.VisioGeneration;
using System.IO;
using Microsoft.Extensions.Logging;

namespace DiagramCore.Controllers
{
    [ApiController]
    [Route("api/visio")]
    public class VisioController : ControllerBase
    {
        private readonly VisioRenderer _renderer;
        private readonly ILogger<VisioController> _logger;

        public VisioController(VisioRenderer renderer, ILogger<VisioController> logger) => (_renderer, _logger) = (renderer, logger);

        [HttpPost("convert")]
        public async Task<IActionResult> ConvertVisio(IFormFile file)
        {
            try
            {
                if (file == null || file.Length == 0)
                    return BadRequest("No file uploaded");
                
                if (file.Length > 50 * 1024 * 1024)
                    return BadRequest("File size exceeds 50MB limit");
                
                if (!IsValidVisioFile(file))
                    return BadRequest("Invalid Visio file format");

                await using var stream = new MemoryStream();
                await file.CopyToAsync(stream);
                
                if (!IsValidVisioContent(stream))
                    return BadRequest("Malformed Visio document");
                
                var svgs = await _renderer.ConvertToSvgs(stream);
                return Ok(new { pages = svgs });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Conversion failed: {ex}");
                return StatusCode(500, "Internal conversion error");
            }
        }

        private bool IsValidVisioFile(IFormFile file)
        {
            return file.ContentType switch
            {
                "application/vnd.ms-visio.drawing" => true,
                "application/vnd.visio" => true,
                _ => Path.GetExtension(file.FileName).ToLower() == ".vsdx"
            };
        }

        private bool IsValidVisioContent(Stream stream)
        {
            try
            {
                using var diagram = new Aspose.Diagram.Diagram(stream);
                return diagram.Pages.Count > 0;
            }
            catch
            {
                return false;
            }
        }
    }
} 