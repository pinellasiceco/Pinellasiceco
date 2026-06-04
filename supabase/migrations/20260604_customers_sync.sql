-- Pinellas Ice Co. customer sync table
-- Run this in Supabase SQL Editor before enabling sync:
-- https://supabase.com/dashboard/project/kbyqatbkqqhuasbjlcwe/sql

CREATE TABLE IF NOT EXISTS public.customers (
  pid bigint PRIMARY KEY,
  data jsonb NOT NULL DEFAULT '{}',
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Single-user app — disable RLS
ALTER TABLE public.customers DISABLE ROW LEVEL SECURITY;

-- Index for efficient sync queries
CREATE INDEX IF NOT EXISTS customers_updated_at_idx
  ON public.customers(updated_at DESC);
