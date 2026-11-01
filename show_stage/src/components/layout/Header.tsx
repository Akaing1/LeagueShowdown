import { Link } from "react-router-dom";
function Brand() {
  return (
    <Link to="/" className="brand">
      <span className="crest">R</span>
      <span className="brand-copy">
        <span>
          RATS ON <b>THE RIFT</b>
        </span>
        <span className="edition">LEAGUE OF LEGENDS EDITION</span>
      </span>
    </Link>
  );
}
export function Header({ children }: { children?: React.ReactNode }) {
  return (
    <header>
      <Brand />
      <div className="header-right">{children}</div>
    </header>
  );
}
