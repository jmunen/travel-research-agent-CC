export type TravelResearchInput = {
    destination: string;
    tripLength?: string;
    budget?: string;
    travelStyle?: string;
    interests?: string[];
    notes?: string;
  };
  
  export type ResearchResult = {
    title: string;
    url: string;
    text: string;
    source?: string;
  };
  
  export type BoxSaveResult = {
    boxSaved: boolean;
    boxFileName: string | null;
    boxUrl?: string | null;
    error?: string;
  };