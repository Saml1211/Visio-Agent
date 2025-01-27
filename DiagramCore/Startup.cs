using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Http.Resilience;
using System;

namespace DiagramCore
{
    public class Startup
    {
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddScoped<ILldFeatureExtractor, LldFeatureExtractor>();
            services.AddSingleton<IModelRegistry, ModelRegistry>();
            services.AddHttpClient<IModelService, ModelService>()
                .AddPolicyHandler(Policy.Handle<Exception>()
                    .CircuitBreakerAsync(5, TimeSpan.FromMinutes(1)));
        }
    }
} 