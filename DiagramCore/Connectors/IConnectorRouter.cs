public interface IConnectorRouter
{
    ConnectorRoute CalculateRoute(Point start, Point end, IEnumerable<Shape> obstacles);
}

public enum ConnectorType
{
    Orthogonal,
    Curved,
    Straight
} 