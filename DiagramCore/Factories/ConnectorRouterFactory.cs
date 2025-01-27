using System;
using System.Collections.Generic;
using DiagramCore.Connectors;
using DiagramCore.Config;

public class ConnectorRouterFactory
{
    public IConnectorRouter CreateRouter(ConnectorRoutingConfig config, Shape startShape, Shape endShape)
    {
        var connectorType = config.DefaultConnectorType;
        
        // Check for shape-specific overrides
        if(config.ShapeTypeOverrides.TryGetValue(startShape.GetType(), out var overrideType) ||
           config.ShapeTypeOverrides.TryGetValue(endShape.GetType(), out overrideType))
        {
            connectorType = overrideType;
        }
        
        return connectorType switch
        {
            ConnectorType.Orthogonal => new OrthogonalRouter(),
            ConnectorType.Curved => new CurvedRouter(),
            ConnectorType.Straight => new StraightLineRouter(),
            _ => throw new NotSupportedException()
        };
    }
} 