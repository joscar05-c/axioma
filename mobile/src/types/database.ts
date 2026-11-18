export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  __InternalSupabase: {
    PostgrestVersion: "14.18";
  };
  public: {
    Tables: {
      daily_usage: {
        Row: {
          solve_count: number;
          updated_at: string;
          usage_date: string;
          user_id: string;
        };
        Insert: {
          solve_count?: number;
          updated_at?: string;
          usage_date?: string;
          user_id: string;
        };
        Update: {
          solve_count?: number;
          updated_at?: string;
          usage_date?: string;
          user_id?: string;
        };
        Relationships: [];
      };
      problems: {
        Row: {
          created_at: string;
          engine_metadata: Json;
          id: string;
          image_path: string | null;
          input_type: "text" | "latex" | "image";
          is_favorite: boolean;
          plot_data: Json | null;
          raw_input: string | null;
          solution_summary: string | null;
          steps_json: Json;
          subject: "math" | "physics" | "chemistry" | "engineering";
          user_id: string;
          verified_result_latex: string | null;
        };
        Insert: {
          created_at?: string;
          engine_metadata?: Json;
          id?: string;
          image_path?: string | null;
          input_type: "text" | "latex" | "image";
          is_favorite?: boolean;
          plot_data?: Json | null;
          raw_input?: string | null;
          solution_summary?: string | null;
          steps_json?: Json;
          subject: "math" | "physics" | "chemistry" | "engineering";
          user_id: string;
          verified_result_latex?: string | null;
        };
        Update: {
          created_at?: string;
          engine_metadata?: Json;
          id?: string;
          image_path?: string | null;
          input_type?: "text" | "latex" | "image";
          is_favorite?: boolean;
          plot_data?: Json | null;
          raw_input?: string | null;
          solution_summary?: string | null;
          steps_json?: Json;
          subject?: "math" | "physics" | "chemistry" | "engineering";
          user_id?: string;
          verified_result_latex?: string | null;
        };
        Relationships: [];
      };
      profiles: {
        Row: {
          created_at: string;
          email: string | null;
          full_name: string | null;
          id: string;
          plan_tier: "free" | "pro";
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          email?: string | null;
          full_name?: string | null;
          id: string;
          plan_tier?: "free" | "pro";
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          email?: string | null;
          full_name?: string | null;
          id?: string;
          plan_tier?: "free" | "pro";
          updated_at?: string;
        };
        Relationships: [];
      };
      subscriptions: {
        Row: {
          created_at: string;
          current_period_end: string | null;
          external_customer_id: string | null;
          id: string;
          provider: "revenuecat" | "stripe";
          status: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          created_at?: string;
          current_period_end?: string | null;
          external_customer_id?: string | null;
          id?: string;
          provider: "revenuecat" | "stripe";
          status: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          created_at?: string;
          current_period_end?: string | null;
          external_customer_id?: string | null;
          id?: string;
          provider?: "revenuecat" | "stripe";
          status?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      consume_daily_solve: {
        Args: { p_limit: number; p_user_id: string };
        Returns: {
          allowed: boolean;
          current_count: number;
          remaining: number;
        }[];
      };
      refund_daily_solve: { Args: { p_user_id: string }; Returns: undefined };
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};
