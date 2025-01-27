import { useState } from 'react';
import { useSupabase } from '../supabaseContext';

type DatabaseConfig = {
  dbPath: string;
  supabaseUrl: string;
  supabaseKey: string;
  encryption: boolean;
};

export default function SetupWizard() {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<DatabaseConfig>({
    dbPath: '/usr/local/visio-data',
    supabaseUrl: 'http://localhost:8000',
    supabaseKey: '',
    encryption: true
  });

  const handleSubmit = async () => {
    // Save configuration
    await fetch('/api/setup', {
      method: 'POST',
      body: JSON.stringify(config)
    });
    
    // Initialize services
    const { initServices } = useSupabase();
    await initServices(config);
    
    // Reload app
    window.location.reload();
  };

  return (
    <div className="setup-wizard">
      <h1>Visio Agent Setup</h1>
      
      {step === 1 && (
        <DatabaseConfigStep 
          config={config}
          onChange={setConfig}
          next={() => setStep(2)}
        />
      )}
      
      {step === 2 && (
        <SecuritySettingsStep
          config={config}
          onChange={setConfig}
          submit={handleSubmit}
        />
      )}
    </div>
  );
}

function DatabaseConfigStep({ config, onChange, next }) {
  return (
    <div>
      <h2>Database Configuration</h2>
      <input
        type="text"
        value={config.dbPath}
        onChange={(e) => onChange({...config, dbPath: e.target.value})}
        placeholder="Database storage path"
      />
      <input
        type="text"
        value={config.supabaseUrl}
        onChange={(e) => onChange({...config, supabaseUrl: e.target.value})}
        placeholder="Supabase URL"
      />
      <input
        type="password"
        value={config.supabaseKey}
        onChange={(e) => onChange({...config, supabaseKey: e.target.value})}
        placeholder="Supabase Key"
      />
      <button onClick={next}>Next</button>
    </div>
  );
} 