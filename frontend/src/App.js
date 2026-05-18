import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Generator from "@/pages/Generator";
import { Toaster } from "sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Generator />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="bottom-right" richColors closeButton />
    </div>
  );
}

export default App;
