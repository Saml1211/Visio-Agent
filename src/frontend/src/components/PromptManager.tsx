import React, { useState } from 'react';

interface PromptEditorProps {
  prompts: PromptConfig[];
  onSave: (name: string, version: string, content: string) => void;
}

const PromptEditor: React.FC<PromptEditorProps> = ({ prompts, onSave }) => {
  const [selectedPrompt, setSelectedPrompt] = useState<PromptConfig>();
  const [editContent, setEditContent] = useState('');

  return (
    <div className="prompt-manager">
      <div className="prompt-list">
        {prompts.map(prompt => (
          <div key={prompt.name} className="prompt-item">
            <h3>{prompt.name}</h3>
            {prompt.versions.map(version => (
              <div key={version.version} className="version-item">
                <span>v{version.version}</span>
                <button onClick={() => {
                  setSelectedPrompt(prompt);
                  setEditContent(version.content);
                }}>
                  Edit
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
      
      {selectedPrompt && (
        <div className="prompt-editor">
          <textarea 
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={10}
          />
          <button onClick={() => onSave(selectedPrompt.name, selectedPrompt.versions[0].version, editContent)}>
            Save Changes
          </button>
        </div>
      )}
    </div>
  );
};

export default PromptEditor; 