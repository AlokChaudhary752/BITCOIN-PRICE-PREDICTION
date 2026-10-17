import React, { useEffect, useState } from "react";
import { Smile, Frown, Meh, TrendingUp, Newspaper, Activity } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";

export const SentimentView: React.FC = () => {
  const [sentiment, setSentiment] = useState<any>(null);

  useEffect(() => {
    fetch("/api/v1/analysis/sentiment")
      .then((r) => r.json())
      .then((d) => setSentiment(d))
      .catch((e) => console.error(e));
  }, []);

  const history = sentiment?.history_30d || [];
  const currentScore = sentiment?.current_score || 72;
  const classification = sentiment?.classification || "Greed";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Smile className="w-5 h-5 text-gold-500" /> Market Sentiment & Headline Polarity
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Alternative.me Crypto Fear & Greed index combined with NLP sentiment scoring.
          </p>
        </div>
        <Badge variant={currentScore > 55 ? "bullish" : currentScore < 45 ? "bearish" : "gold"} size="md">
          {classification} ({currentScore}/100)
        </Badge>
      </div>

      {/* STATS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Stat
          label="Current Fear & Greed"
          value={`${currentScore} / 100`}
          subtext={`Classification: ${classification}`}
          variant={currentScore > 55 ? "bullish" : currentScore < 45 ? "bearish" : "gold"}
        />
        <Stat
          label="Rolling Sentiment Index"
          value={`${((sentiment?.rolling_sentiment_index || 0.72) * 100).toFixed(1)}%`}
          subtext="Normalized 0..1 Scale"
          variant="default"
        />
        <Stat
          label="Headline Sentiment"
          value="+0.42"
          subtext="Net Bullish Bias"
          variant="bullish"
        />
      </div>

      {/* 30-DAY FEAR & GREED CHART */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <Card className="p-5">
            <CardHeader>
              <CardTitle>30-Day Historical Sentiment Trend</CardTitle>
              <Badge variant="outline" size="sm">0 (Extreme Fear) - 100 (Extreme Greed)</Badge>
            </CardHeader>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2638" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10, fontFamily: "JetBrains Mono" }} tickFormatter={(d) => d.slice(5)} />
                  <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#0c1017", borderColor: "#1c2638", fontSize: "11px", fontFamily: "JetBrains Mono" }} />
                  <Bar dataKey="value" fill="#f59e0b" name="Fear & Greed Index" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* HEADLINE POLARITY FEED */}
        <div className="lg:col-span-4">
          <Card className="p-5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Newspaper className="w-4 h-4 text-gold-500" /> Recent News Polarity
              </CardTitle>
              <Badge variant="gold" size="sm">NLP Scored</Badge>
            </CardHeader>

            <div className="space-y-3">
              {(sentiment?.sample_headlines || []).map((h: any, i: number) => (
                <div key={i} className="p-3 rounded-lg bg-surface/70 border border-border/50 space-y-1.5">
                  <p className="text-xs text-slate-200 leading-snug">{h.title}</p>
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-500">Polarity: {h.polarity > 0 ? "+" : ""}{h.polarity}</span>
                    <Badge variant={h.impact === "bullish" ? "bullish" : h.impact === "bearish" ? "bearish" : "outline"} size="sm">
                      {h.impact}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
