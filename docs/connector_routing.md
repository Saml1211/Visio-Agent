## Routing Configuration Options

```yaml
routing:
  default_style: orthogonal
  grid_spacing: 5.0
  optimization:
    minimize_crossings: true
    group_parallel_lines: true
  styles:
    network: 
      style: orthogonal
      spacing: 10.0
    flowchart:
      style: curved  
```

**Visual Examples**  
![Routing Comparison](docs/images/routing_comparison.png) 