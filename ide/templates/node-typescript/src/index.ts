import { createServer } from "http";

const port = Number(process.env.PORT ?? 3000);

createServer((_req, res) => {
  res.writeHead(200, { "content-type": "text/plain" });
  res.end("hello from your typescript celaut service\n");
}).listen(port, "0.0.0.0", () =>
  console.log(`ts celaut service listening on ${port}`)
);
