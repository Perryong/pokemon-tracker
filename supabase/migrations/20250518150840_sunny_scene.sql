/*
  # Initial Schema Setup for Card Collection System

  1. New Tables
    - `users`
      - `id` (uuid, primary key) - User's unique identifier
      - `username` (text, unique) - User's unique username
      - `email` (text) - User's email from auth.users
      - `created_at` (timestamptz) - Account creation timestamp
      - `last_login` (timestamptz) - Last login timestamp
    
    - `cards`
      - `id` (uuid, primary key) - Card's unique identifier
      - `name` (text) - Card name
      - `type` (text) - Card type/category
      - `rarity` (text) - Card rarity level
      - `release_date` (date) - Card release date
      - `description` (text) - Card description
      - `image_url` (text) - URL to card image
      - `created_at` (timestamptz) - Record creation timestamp
      - `updated_at` (timestamptz) - Record update timestamp
    
    - `user_cards`
      - `id` (uuid, primary key) - Collection entry unique identifier
      - `user_id` (uuid) - Reference to users table
      - `card_id` (uuid) - Reference to cards table
      - `acquisition_date` (date) - Date when card was acquired
      - `condition_rating` (integer) - Card condition (1-10)
      - `notes` (text) - User notes about the card
      - `quantity` (integer) - Number of copies owned
      - `created_at` (timestamptz) - Record creation timestamp
      - `updated_at` (timestamptz) - Record update timestamp

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
    - Secure user data access
    - Protect card collection data

  3. Indexes
    - Username and email indexes for users
    - Card name and type indexes
    - Collection lookup indexes
*/

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username text UNIQUE NOT NULL,
  email text,
  created_at timestamptz DEFAULT now(),
  last_login timestamptz DEFAULT now(),
  CONSTRAINT users_email_check CHECK (email ~* '^.+@.+\..+$')
);

CREATE INDEX IF NOT EXISTS users_username_idx ON users (username);
CREATE INDEX IF NOT EXISTS users_email_idx ON users (email);

-- Create cards table
CREATE TABLE IF NOT EXISTS cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  type text NOT NULL,
  rarity text NOT NULL,
  release_date date NOT NULL,
  description text,
  image_url text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS cards_name_idx ON cards (name);
CREATE INDEX IF NOT EXISTS cards_type_idx ON cards (type);
CREATE INDEX IF NOT EXISTS cards_rarity_idx ON cards (rarity);
CREATE INDEX IF NOT EXISTS cards_release_date_idx ON cards (release_date);

-- Create user_cards table
CREATE TABLE IF NOT EXISTS user_cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  card_id uuid NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
  acquisition_date date DEFAULT CURRENT_DATE,
  condition_rating integer NOT NULL CHECK (condition_rating BETWEEN 1 AND 10),
  notes text,
  quantity integer NOT NULL DEFAULT 1 CHECK (quantity > 0),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id, card_id)
);

CREATE INDEX IF NOT EXISTS user_cards_user_id_idx ON user_cards (user_id);
CREATE INDEX IF NOT EXISTS user_cards_card_id_idx ON user_cards (card_id);
CREATE INDEX IF NOT EXISTS user_cards_acquisition_date_idx ON user_cards (acquisition_date);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_cards ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view their own profile"
  ON users
  FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON users
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Create policies for cards table
CREATE POLICY "Anyone can view cards"
  ON cards
  FOR SELECT
  TO authenticated
  USING (true);

-- Create policies for user_cards table
CREATE POLICY "Users can view their own collection"
  ON user_cards
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own collection"
  ON user_cards
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Create function to handle updated_at
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_cards_updated_at
  BEFORE UPDATE ON cards
  FOR EACH ROW
  EXECUTE FUNCTION handle_updated_at();

CREATE TRIGGER update_user_cards_updated_at
  BEFORE UPDATE ON user_cards
  FOR EACH ROW
  EXECUTE FUNCTION handle_updated_at();

-- Create function to handle new user creation
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO users (id, email, username)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'username', 'user_' || substr(NEW.id::text, 1, 8))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic user profile creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();