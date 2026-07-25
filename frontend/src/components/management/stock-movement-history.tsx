import type { VariantStockHistory } from "@/lib/management-inventory";

function signed(value: number) {
  return value > 0 ? `+${value}` : String(value);
}

export function StockMovementHistory({
  history,
}: {
  history: VariantStockHistory;
}) {
  return (
    <div className="stock-history">
      <section className="inventory-dashboard__totals">
        {history.current_stock.map((stock) => (
          <div key={stock.id}>
            <strong>{stock.quantity_available}</strong>
            <span>{stock.branch_name} available</span>
            <small>{stock.quantity_on_hand} on hand / {stock.quantity_reserved} reserved</small>
          </div>
        ))}
      </section>
      {!history.movements.length ? (
        <section className="empty-state"><h2>No movement history yet</h2><p>Future opening balances, adjustments, reservations, sales, returns, and transfers will appear here.</p></section>
      ) : (
        <ol className="stock-history__timeline">
          {history.movements.map((movement) => (
            <li key={movement.id}>
              <div className={`stock-history__marker stock-history__marker--${movement.movement_type}`} aria-hidden="true" />
              <article>
                <header>
                  <div><strong>{movement.movement_label}</strong><span>{movement.branch_name} / {movement.branch_code}</span></div>
                  <time dateTime={movement.created_at}>{new Intl.DateTimeFormat("en-GH", { dateStyle: "medium", timeStyle: "short" }).format(new Date(movement.created_at))}</time>
                </header>
                <dl>
                  <div><dt>On-hand change</dt><dd className={movement.quantity_on_hand_change < 0 ? "stock-history__negative" : "stock-history__positive"}>{signed(movement.quantity_on_hand_change)}</dd></div>
                  <div><dt>Reserved change</dt><dd className={movement.quantity_reserved_change < 0 ? "stock-history__negative" : "stock-history__positive"}>{signed(movement.quantity_reserved_change)}</dd></div>
                  <div><dt>Balance after</dt><dd>{movement.quantity_on_hand_after} on hand / {movement.quantity_reserved_after} reserved</dd></div>
                </dl>
                {movement.note ? <p>{movement.note}</p> : null}
                <footer><span>By {movement.performed_by_name}</span>{movement.reference_id ? <span>{movement.reference_type}: {movement.reference_id}</span> : null}</footer>
              </article>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
