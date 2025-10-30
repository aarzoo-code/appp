import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center">
      <div className="max-w-2xl text-center p-8">
        <h1 className="text-4xl font-bold mb-4 text-foreground">Welcome to AI Lab</h1>
        <p className="text-muted-foreground mb-6">Gamified AI learning platform — pick where to go next.</p>
        <div className="flex gap-4 justify-center">
          <Link to="/dashboard" className="inline-block px-4 py-2 rounded bg-primary text-primary-foreground">
            Dashboard
          </Link>
          <Link to="/roadmap" className="inline-block px-4 py-2 rounded border border-border text-foreground">
            Roadmap
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Index;
