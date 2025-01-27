using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using YamlDotNet.Serialization;

public class PromptConfig
{
    public string Name { get; set; }
    public string Description { get; set; }
    public List<PromptVersion> Versions { get; set; } = new();
}

public class PromptVersion
{
    public string Version { get; set; }
    public string Content { get; set; }
    public Dictionary<string, object> Metadata { get; set; } = new();
}

public class PromptManager
{
    private readonly Dictionary<string, PromptConfig> _prompts = new();
    
    public void LoadPrompts(string directoryPath)
    {
        foreach (var file in Directory.EnumerateFiles(directoryPath, "*.yaml"))
        {
            var configs = new YamlLoader().Load<PromptConfig>(file);
            foreach (var config in configs)
            {
                _prompts[config.Name] = config;
            }
        }
    }
    
    public string GetPrompt(string name, string version = null)
    {
        if (!_prompts.TryGetValue(name, out var config))
            throw new PromptNotFoundException(name);
        
        var versionToUse = version != null 
            ? config.Versions.FirstOrDefault(v => v.Version == version)
            : config.Versions.OrderByDescending(v => v.Version).FirstOrDefault();
        
        return versionToUse?.Content ?? throw new PromptVersionNotFoundException(name, version);
    }
    
    public string RenderPrompt(string name, Dictionary<string, object> parameters, string version = null)
    {
        var template = GetPrompt(name, version);
        return TemplateEngine.Render(template, parameters);
    }
} 