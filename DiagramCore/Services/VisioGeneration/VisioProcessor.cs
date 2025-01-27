using System;
using System.IO;

public class VisioProcessor : IDisposable
{
    private Aspose.Diagram.Diagram _diagram;
    private bool _disposed;

    public void Load(Stream stream)
    {
        _diagram?.Dispose();
        _diagram = new Aspose.Diagram.Diagram(stream);
    }

    public void Dispose()
    {
        if (_disposed) return;
        _diagram?.Dispose();
        _disposed = true;
        GC.SuppressFinalize(this);
    }
} 