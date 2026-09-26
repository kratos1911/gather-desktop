export interface Sample {
  id: string;
  title: string;
  category: "Documents" | "Presentations" | "Photos";
  extension: string;
  description: string;
  location: string;
  heading: string;
  content: string;
  cover: string;
  art: string;
}
export const samples: Sample[] = [
  {
    id: "research",
    title: "The art of remembering",
    category: "Documents",
    extension: "PDF",
    description: "Notes on memory, meaning, and how we find things.",
    location: "Page 1",
    heading: "Meaning creates a way back.",
    cover: "THE ART OF\nREMEMBERING",
    art: "sage",
    content:
      "We rarely remember the exact name of a file. We remember the question it answered, the person who shared it, or the idea it helped us understand.\n\nA useful personal library connects those fragments to their source. This fictional research note explores how concepts can provide another route to information.\n\nThis is a hand-written interface fixture, not an uploaded PDF or a generated answer.",
  },
  {
    id: "launch",
    title: "A quieter kind of workspace",
    category: "Presentations",
    extension: "PPTX",
    description: "A concept deck for a more thoughtful digital space.",
    location: "Slide 1",
    heading: "Make room for what matters.",
    cover: "LESS NOISE.\nMORE CLARITY.",
    art: "lavender",
    content:
      "A workspace should make the next useful action obvious. Search, preview, and a clear source are the central parts of this concept.\n\nThe launch plan has three stages: validate the experience, connect real retrieval, and test the complete workflow.\n\nThis is a synthetic slide excerpt. Real PowerPoint rendering is not connected.",
  },
  {
    id: "coast",
    title: "An afternoon by the coast",
    category: "Photos",
    extension: "JPG",
    description: "A sample photo entry for future visual search.",
    location: "Placeholder artwork",
    heading: "The visual side of your library.",
    cover: "COASTAL\nCOLLECTION",
    art: "sand",
    content:
      "This entry represents a photograph of a quiet coastline. The thumbnail is decorative interface artwork, not an indexed photograph.\n\nWhen visual search is connected, an image model will help match descriptions such as sea, shoreline, and beach to actual imported photos.",
  },
  {
    id: "notes",
    title: "Little ideas, collected",
    category: "Documents",
    extension: "DOCX",
    description: "Research questions and notes for the next project.",
    location: "Section 1",
    heading: "Start with a better question.",
    cover: "FIELD NOTES\nNO. 004",
    art: "blue",
    content:
      "How can someone find information without knowing which folder contains it? How do we explain why a particular result appeared?\n\nOur research questions focus on trust: showing the original source, making processing status clear, and distinguishing evidence from a generated explanation.",
  },
];
export const models = [
  {
    role: "Document search",
    name: "EmbeddingGemma 300M",
    id: "google/embeddinggemma-300m",
    description:
      "Turns text passages into searchable vectors. Compact first candidate; quality and dimensions will be benchmarked.",
  },
  {
    role: "Visual search",
    name: "SigLIP 2 Base",
    id: "google/siglip2-base-patch16-224",
    description:
      "Connects photographs with natural-language descriptions using a separate visual index.",
  },
  {
    role: "Document & image chat",
    name: "Qwen3.5 4B",
    id: "Qwen/Qwen3.5-4B",
    description:
      "Answers questions from selected evidence. A supported 4-bit runtime and memory budget remain to be validated.",
  },
  {
    role: "Scans & screenshots",
    name: "PaddleOCR PP-OCRv5",
    id: "PaddlePaddle/PP-OCRv5_mobile_rec",
    description:
      "Recognition component for an OCR pipeline; detection and language coverage will be configured separately.",
  },
];
