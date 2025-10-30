import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import { CheckCircle2, Lock, Circle, Trophy, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

const Roadmap = () => {
  const levels = [
    {
      level: 1,
      title: "Foundations",
      description: "Python, Git, VSCode, Jupyter basics",
      status: "completed",
      xp: 500,
      skills: ["Python Basics", "Git & GitHub", "VSCode Setup", "Jupyter Notebooks"],
    },
    {
      level: 2,
      title: "Data Fundamentals",
      description: "NumPy, Pandas, Matplotlib, Seaborn",
      status: "in-progress",
      xp: 800,
      skills: ["NumPy Arrays", "Pandas DataFrames", "Data Visualization", "Statistical Analysis"],
    },
    {
      level: 3,
      title: "Machine Learning Basics",
      description: "Scikit-learn, Data Cleaning, Feature Engineering",
      status: "in-progress",
      xp: 1200,
      skills: ["Regression Models", "Classification", "Feature Engineering", "Model Evaluation"],
    },
    {
      level: 4,
      title: "Deep Learning",
      description: "TensorFlow, PyTorch, CNNs, NLP",
      status: "locked",
      xp: 1500,
      skills: ["Neural Networks", "CNNs", "RNNs", "Transfer Learning"],
    },
    {
      level: 5,
      title: "Data Visualization Pro",
      description: "Power BI, Tableau, SQL",
      status: "locked",
      xp: 1000,
      skills: ["Advanced SQL", "Power BI Dashboards", "Tableau Reports", "Data Storytelling"],
    },
    {
      level: 6,
      title: "GenAI & LLMs",
      description: "LangChain, Hugging Face, OpenAI",
      status: "locked",
      xp: 2000,
      skills: ["Prompt Engineering", "LangChain", "Fine-tuning", "RAG Systems"],
    },
    {
      level: 7,
      title: "MLOps & Deployment",
      description: "Docker, Streamlit, FastAPI, MLflow",
      status: "locked",
      xp: 1800,
      skills: ["Docker Containers", "API Development", "Model Deployment", "CI/CD Pipelines"],
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-6 h-6 text-success" />;
      case "in-progress":
        return <Circle className="w-6 h-6 text-primary animate-pulse" />;
      case "locked":
        return <Lock className="w-6 h-6 text-muted-foreground" />;
      default:
        return <Circle className="w-6 h-6 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "border-success bg-success/10";
      case "in-progress":
        return "border-primary bg-primary/10 shadow-glow";
      case "locked":
        return "border-border bg-muted/50";
      default:
        return "border-border";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero">
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary">
            AI Lab
          </Link>
          <Link to="/dashboard">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12 animate-slide-up">
          <Trophy className="w-16 h-16 text-primary mx-auto mb-4 animate-float" />
          <h1 className="text-5xl font-bold mb-4 text-foreground">Learning Roadmap</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Master AI, ML, and Data Science through 7 progressive levels
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-6">
          {levels.map((level, index) => (
            <Card
              key={index}
              className={`p-6 transition-all hover:scale-[1.02] ${getStatusColor(
                level.status
              )} border-2 animate-slide-in`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">{getStatusIcon(level.status)}</div>
                <div className="flex-grow">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={level.status === "locked" ? "outline" : "default"}
                        className="text-lg px-3 py-1"
                      >
                        Level {level.level}
                      </Badge>
                      <h3 className="text-2xl font-bold text-foreground">{level.title}</h3>
                    </div>
                    <Badge variant="outline" className="text-sm">
                      {level.xp} XP
                    </Badge>
                  </div>
                  <p className="text-muted-foreground mb-4">{level.description}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {level.skills.map((skill, skillIndex) => (
                      <Badge
                        key={skillIndex}
                        variant="secondary"
                        className={level.status === "locked" ? "opacity-50" : ""}
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                  {level.status !== "locked" && (
                    <Button
                      variant={level.status === "in-progress" ? "default" : "outline"}
                      size="sm"
                    >
                      {level.status === "completed" ? "Review Labs" : "Continue Learning"}
                    </Button>
                  )}
                  {level.status === "locked" && (
                    <p className="text-sm text-muted-foreground italic">
                      Complete previous levels to unlock
                    </p>
                  )}
                </div>
              </div>

              {/* Connector Line */}
              {index < levels.length - 1 && (
                <div className="ml-3 mt-4 mb-0 h-8 w-0.5 bg-border"></div>
              )}
            </Card>
          ))}
        </div>

        {/* Summary Card */}
        <Card className="mt-12 p-8 bg-gradient-secondary border-0 shadow-card max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-foreground mb-4 text-center">
            Your AI Journey Awaits
          </h3>
          <p className="text-center text-muted-foreground mb-6">
            Complete all 7 levels to become a certified AI Engineer. Each level builds upon the
            previous one, ensuring a solid foundation.
          </p>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-3xl font-bold text-primary">7</p>
              <p className="text-sm text-muted-foreground">Total Levels</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-warning">8,800</p>
              <p className="text-sm text-muted-foreground">Total XP</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-accent">25+</p>
              <p className="text-sm text-muted-foreground">Core Skills</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Roadmap;
