const express = require("express");
const app = express();
const port = process.env.PORT || 3000;

app.get("/health", (_req, res) => res.json({ status: "ok" }));
app.post("/process", express.json(), (req, res) =>
  res.json({ received: req.body ?? null })
);

app.listen(port, "0.0.0.0", () =>
  console.log(`node celaut service listening on ${port}`)
);
