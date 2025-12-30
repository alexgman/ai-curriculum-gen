export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  thinkingSteps?: string[];
  thinkingContent?: string; // Extended thinking from Claude
  researchPhase?: string; // Current research phase
  phaseNumber?: number; // Phase number (1, 2, 3)
  totalPhases?: number; // Total phases (3)
  needsClarification?: boolean; // Waiting for user feedback
  clarificationQuestion?: string; // Clarification question
  canDownloadReport?: boolean; // Final report ready
}

export interface ToolCall {
  name: string;
  arguments: Record<string, any>;
  result?: any;
}

export interface ResearchSession {
  id: string;
  title: string;
  createdAt: string;
  messages: Message[];
  industry?: string;
  researchData?: ResearchData;
  thinkingStatus?: string | null;
  isGeneratingTitle?: boolean;
  isEditingTitle?: boolean; // Title edit mode
  currentPhase?: string; // Current research phase
  phaseNumber?: number; // Phase number
  totalPhases?: number; // Total phases
}

export interface ResearchData {
  competitors: Competitor[];
  curricula: Curriculum[];
  redditPosts: RedditPost[];
  podcasts: Podcast[];
  blogs: Blog[];
}

export interface Competitor {
  name: string;
  url: string;
  price?: string;
  priceTier?: string;
  popularityRank?: number;
}

export interface Curriculum {
  courseName: string;
  provider: string;
  modules: Module[];
  certifications?: string[];
}

export interface Module {
  title: string;
  lessons: string[];
  description?: string;
}

export interface RedditPost {
  id: string;
  title: string;
  subreddit: string;
  score: number;
  url: string;
  content?: string;
}

export interface Podcast {
  name: string;
  url: string;
  description?: string;
}

export interface Blog {
  name: string;
  url: string;
  description?: string;
}

