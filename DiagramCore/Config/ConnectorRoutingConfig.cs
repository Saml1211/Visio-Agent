public class ConnectorRoutingConfig
{
    public ConnectorType DefaultConnectorType { get; set; } = ConnectorType.Orthogonal;
    public Dictionary<Type, ConnectorType> ShapeTypeOverrides { get; } = new();
    public int RoutingPadding { get; set; } = 10;
    public bool OptimizeCrossings { get; set; } = true;
} 