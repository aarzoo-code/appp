import { Card } from "@/components/card";
import { Progress } from "@/components/progress";
import { Badge } from "@/components/badge";
import { Button } from "@/components/button";
import { Award, BookOpen, Code, Flame, Github, TrendingUp, Zap } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const Dashboard = () => {
  const navigate = useNavigate();

  const [stats, setStats] = useState(() => {
    try {
      const raw = localStorage.getItem("ai:stats");
      return raw ? JSON.parse(raw) : { xp: 2450, level: 3, streak: 12, nextLevelXp: 3000, badges: 8, completedLabs: 24 };
    } catch (e) {
      return { xp: 2450, level: 3, streak: 12, nextLevelXp: 3000, badges: 8, completedLabs: 24 };
    }
  });

  const [recentActivity, setRecentActivity] = useState(() => {
    try {
      const raw = localStorage.getItem("ai:recent");
      return raw
        ? JSON.parse(raw)
        : [
            { title: "Completed: Pandas DataFrames", xp: 150, time: "2 hours ago" },
            { title: "Completed: NumPy Arrays", xp: 120, time: "1 day ago" },
            { title: "Challenge: Data Cleaning", xp: 200, time: "2 days ago" },
          ];
    } catch (e) {
      return [
        { title: "Completed: Pandas DataFrames", xp: 150, time: "2 hours ago" },
        { title: "Completed: NumPy Arrays", xp: 120, time: "1 day ago" },
        { title: "Challenge: Data Cleaning", xp: 200, time: "2 days ago" },
      ];
    }
  });

  const [currentLabs, setCurrentLabs] = useState(() => {
    try {
      const raw = localStorage.getItem("ai:currentLabs");
      return raw ? JSON.parse(raw) : [{ title: "Matplotlib Visualization", progress: 65, level: 2 }, { title: "Scikit-learn Basics", progress: 30, level: 3 }];
    } catch (e) {
      return [{ title: "Matplotlib Visualization", progress: 65, level: 2 }, { title: "Scikit-learn Basics", progress: 30, level: 3 }];
    }
  });

  const [githubConnected, setGithubConnected] = useState(() => {
    try {
      return localStorage.getItem("ai:github_connected") === "true";
    } catch (e) {
      return false;
    }
  });

  const [lastLab, setLastLab] = useState<string | null>(() => {
    try {
      return localStorage.getItem("ai:last_lab");
    } catch (e) {
      return null;
    }
  });

  useEffect(() => {
    localStorage.setItem("ai:stats", JSON.stringify(stats));
  }, [stats]);

  useEffect(() => {
    localStorage.setItem("ai:currentLabs", JSON.stringify(currentLabs));
  }, [currentLabs]);

  useEffect(() => {
    localStorage.setItem("ai:recent", JSON.stringify(recentActivity));
  }, [recentActivity]);

  useEffect(() => {
    localStorage.setItem("ai:github_connected", githubConnected ? "true" : "false");
  }, [githubConnected]);

  useEffect(() => {
    if (lastLab) localStorage.setItem("ai:last_lab", lastLab);
  }, [lastLab]);

  const resumeLastLab = () => {
    if (lastLab) {
      navigate("/lab");
    }
  };

  const startLab = (labTitle: string) => {
    setLastLab(labTitle);
    // Navigate to lab environment stub
    navigate("/lab");
  };

  const toggleGithub = () => {
    // Mock GitHub connect flow; in reality you would do OAuth
    setGithubConnected((v) => !v);
  };

  return (
    <div className="min-h-screen bg-gradient-hero">
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary">
            AI Lab
          </Link>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={toggleGithub}>
              <Github className="w-4 h-4 mr-2" />
              {githubConnected ? "Disconnect GitHub" : "Connect GitHub"}
            </Button>
            <Button variant="default" size="sm">
              <BookOpen className="w-4 h-4 mr-2" />
              Browse Labs
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-6 bg-gradient-primary border-0 shadow-glow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-primary-foreground/80 mb-1">Level</p>
                <p className="text-4xl font-bold text-primary-foreground">{stats.level}</p>
              </div>
              <Award className="w-12 h-12 text-primary-foreground/50" />
            </div>
          </Card>

          <Card className="p-6 bg-card border-border shadow-card hover:shadow-glow transition-all">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Total XP</p>
                <p className="text-4xl font-bold text-foreground">{stats.xp}</p>
              </div>
              <Zap className="w-12 h-12 text-primary animate-pulse-glow" />
            </div>
          </Card>

          <Card className="p-6 bg-card border-border shadow-card hover:shadow-glow transition-all">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Day Streak</p>
                <p className="text-4xl font-bold text-warning">{stats.streak}</p>
              </div>
              <Flame className="w-12 h-12 text-warning" />
            </div>
          </Card>

          <Card className="p-6 bg-card border-border shadow-card hover:shadow-glow transition-all">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Badges</p>
                <p className="text-4xl font-bold text-accent">{stats.badges}</p>
              </div>
              <Award className="w-12 h-12 text-accent" />
            </div>
          </Card>
        </div>

        {/* Level Progress */}
          <Card className="p-6 mb-8 bg-card border-border shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-foreground">Level {userStats.level} Progress</h3>
            <span className="text-sm text-muted-foreground">
              {stats.xp} / {stats.nextLevelXp} XP
            </span>
          </div>
          <Progress value={(userStats.xp / userStats.nextLevelXp) * 100} className="h-3" />
          <p className="text-sm text-muted-foreground mt-2">
            {stats.nextLevelXp - stats.xp} XP until Level {stats.level + 1}
          </p>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Current Labs */}
          <Card className="p-6 bg-card border-border shadow-card">
            <h3 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
              <Code className="w-5 h-5 text-primary" />
              Continue Learning
            </h3>
            <div className="space-y-4">
              {currentLabs.map((lab, index) => (
                <div
                  key={index}
                  className="p-4 bg-secondary rounded-lg border border-border hover:border-primary transition-all cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-foreground">{lab.title}</h4>
                    <Badge variant="outline">Level {lab.level}</Badge>
                  </div>
                  <Progress value={lab.progress} className="h-2 mb-2" />
                  <p className="text-xs text-muted-foreground">{lab.progress}% complete</p>
                </div>
              ))}
              <Button className="w-full" variant="outline">
                Browse All Labs
              </Button>
            </div>
          </Card>

          {/* Recent Activity */}
          <Card className="p-6 bg-card border-border shadow-card">
            <h3 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-success" />
              Recent Activity
            </h3>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div
                  key={index}
                  className="p-4 bg-secondary rounded-lg border border-border hover:border-success transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-foreground text-sm">{activity.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                    </div>
                    <Badge className="bg-success text-primary-foreground">+{activity.xp} XP</Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="p-6 mt-8 bg-gradient-secondary border-0 shadow-card">
          <h3 className="text-xl font-bold text-foreground mb-4">Quick Start</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="h-auto p-6 flex flex-col items-center gap-2" variant="outline">
              <Code className="w-8 h-8" />
              <span className="font-semibold">Practice Sandbox</span>
              <span className="text-xs text-muted-foreground">Open coding playground</span>
            </Button>
            <Button className="h-auto p-6 flex flex-col items-center gap-2" variant="outline">
              <Award className="w-8 h-8" />
              <span className="font-semibold">Daily Challenge</span>
              <span className="text-xs text-muted-foreground">Earn bonus XP</span>
            </Button>
            <Link to="/roadmap" className="w-full">
              <Button className="h-auto p-6 flex flex-col items-center gap-2 w-full" variant="outline">
                <TrendingUp className="w-8 h-8" />
                <span className="font-semibold">View Roadmap</span>
                <span className="text-xs text-muted-foreground">Track your progress</span>
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
