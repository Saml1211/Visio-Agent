declare interface VisioData {
  pages: VisioPage[];
  metadata: {
    width: number;
    height: number;
    author?: string;
    created?: string;
  };
}

interface VisioPage {
  svg: string;
  pageNumber: number;
  shapes: VisioShape[];
}

interface VisioShape {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
} 