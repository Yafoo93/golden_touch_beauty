export type MetricDefinition = {
  name: string;
  formula: string;
  notes?: string;
};

export type MetricSection = {
  id: string;
  title: string;
  scope: string;
  metrics: MetricDefinition[];
};

export const managementMetricDefinitions: MetricSection[] = [
  {
    id: "overview",
    title: "Management overview",
    scope: "Uses only branches the signed-in manager may access. Date filters replace ‘today’ where supplied; the remaining filters limit all compatible records.",
    metrics: [
      { name: "Appointments", formula: "Count of bookings scheduled in the selected period, excluding cancelled and rejected bookings." },
      { name: "Pending booking requests", formula: "Count of bookings whose current status is Pending." },
      { name: "Proposed changes awaiting acceptance", formula: "Count of Proposed bookings that have a proposed start time and no expiry, or an expiry later than the current time." },
      { name: "Sales", formula: "Sum of successful GHS Payment amounts whose paid date falls in the selected period." },
      { name: "Product revenue", formula: "Sum of successful GHS Payment amounts linked to product orders in scope." },
      { name: "Service revenue", formula: "Sum of successful GHS Payment amounts linked to service bookings in scope." },
      { name: "Outstanding balances", formula: "Sum of total amounts on open GHS invoices in scope." },
      { name: "Pending online orders", formula: "Count of orders in awaiting-payment, payment-under-review, paid, processing, ready-for-pickup, or shipped status." },
      { name: "Low-stock products", formula: "Count of branch inventory records where quantity on hand ≤ quantity reserved + reorder level." },
      { name: "Branch appointments", formula: "Overview Appointments formula, grouped by branch." },
      { name: "Branch sales", formula: "Overview Sales formula, grouped by branch." },
      { name: "Branch pending orders", formula: "Overview Pending online orders formula, grouped by branch." },
      { name: "Branch low stock", formula: "Overview Low-stock products formula, grouped by branch." },
    ],
  },
  {
    id: "sales",
    title: "Sales report",
    scope: "Online revenue uses paid, non-cancelled orders and their payment date. POS revenue uses completed, non-reversed sales and their completion date.",
    metrics: [
      { name: "Total revenue", formula: "Online revenue + POS revenue." },
      { name: "Online revenue", formula: "Sum of total amounts for paid, non-cancelled online orders." },
      { name: "POS revenue", formula: "Sum of total amounts for completed, non-reversed POS sales." },
      { name: "Transactions", formula: "Online order count + completed POS sale count." },
      { name: "Online / POS count", formula: "Count of qualifying transactions from the respective channel." },
      { name: "Online / POS share", formula: "Channel revenue ÷ total revenue × 100; 0% when total revenue is zero." },
      { name: "Average sale", formula: "Total revenue ÷ transaction count; GH₵0 when the count is zero." },
      { name: "Average online order", formula: "Online revenue ÷ online order count; GH₵0 when the count is zero." },
      { name: "Average POS sale", formula: "POS revenue ÷ POS sale count; GH₵0 when the count is zero." },
      { name: "Daily / weekly / monthly sales", formula: "Total qualifying revenue grouped by payment/completion date, calendar week beginning Monday, or calendar month." },
      { name: "Payment-method total", formula: "Sum of successful online Payment and POS Payment Entry amounts grouped by method." },
    ],
  },
  {
    id: "bookings",
    title: "Bookings report",
    scope: "Uses bookings whose preferred appointment start falls in the selected period and permitted branches.",
    metrics: [
      { name: "Booking count", formula: "Count of all bookings matching the selected filters." },
      { name: "Active count", formula: "Booking count − cancelled count − no-show count − rejected count." },
      { name: "Completed / cancelled / no-show / rejected", formula: "Count of matching bookings in the named status." },
      { name: "Cancellation rate", formula: "Cancelled count ÷ booking count × 100; 0% when booking count is zero." },
      { name: "No-show rate", formula: "No-show count ÷ booking count × 100; 0% when booking count is zero." },
      { name: "Booked value", formula: "Sum of snapshotted service-item unit prices for matching bookings, irrespective of payment status." },
      { name: "Average booking value", formula: "Booked value ÷ booking count; GH₵0 when booking count is zero." },
      { name: "Scheduled duration", formula: "Sum of total scheduled booking minutes; displayed in hours by dividing by 60." },
    ],
  },
  {
    id: "products",
    title: "Products report",
    scope: "Combines qualifying online order items and completed POS product lines. Costs use immutable sale-time cost snapshots.",
    metrics: [
      { name: "Products shown", formula: "Count of distinct product variants represented after filters." },
      { name: "Units sold", formula: "Sum of online order-item quantities + completed POS product-line quantities." },
      { name: "Product revenue", formula: "Sum of online and POS product line totals." },
      { name: "Cost of goods sold", formula: "Sum of quantity × sale-time unit-cost snapshot for every qualifying product line." },
      { name: "Gross profit", formula: "Product revenue − cost of goods sold." },
      { name: "Gross margin", formula: "Gross profit ÷ product revenue × 100; 0% when revenue is zero." },
      { name: "Average per unit", formula: "Product revenue ÷ units sold; GH₵0 when units sold is zero." },
      { name: "Available stock", formula: "Current quantity on hand − current quantity reserved." },
      { name: "Low stock", formula: "Count of shown variants where 0 < available stock ≤ reorder level." },
      { name: "Out of stock", formula: "Count of shown variants where available stock ≤ 0." },
      { name: "Best-selling rank", formula: "Descending units sold, with revenue as the tie-breaker; top five are displayed." },
    ],
  },
  {
    id: "services",
    title: "Services report",
    scope: "Demand includes booking service items and completed POS service lines. Booking revenue is recognized only for fully paid, non-cancelled/non-rejected bookings.",
    metrics: [
      { name: "Services delivered/booked", formula: "Booking service-item count + completed POS service-line quantity." },
      { name: "Distinct services", formula: "Count of unique services represented after filters." },
      { name: "Service revenue", formula: "Recognized booking service-item prices + completed POS service-line totals." },
      { name: "Revenue per service activity", formula: "Service revenue ÷ services delivered/booked; GH₵0 when activity is zero." },
      { name: "Completed bookings", formula: "Count of booking service items belonging to completed bookings." },
      { name: "Scheduled hours", formula: "Sum of booking service-item duration minutes ÷ 60." },
      { name: "Popular-service rank", formula: "Descending total booking/POS occurrences, with revenue as the tie-breaker; top five are displayed." },
    ],
  },
  {
    id: "inventory",
    title: "Inventory report",
    scope: "Stock position is current at export/view time. Movement metrics use append-only stock movements occurring in the selected period.",
    metrics: [
      { name: "Inventory records", formula: "Count of branch-and-variant inventory records matching the filters." },
      { name: "Quantity on hand", formula: "Sum of physical quantity-on-hand balances." },
      { name: "Quantity reserved", formula: "Sum of quantities reserved for open transactions." },
      { name: "Quantity available", formula: "Quantity on hand − quantity reserved, summed across shown records." },
      { name: "Cost value", formula: "Sum of quantity on hand × current variant cost price." },
      { name: "Retail value", formula: "Sum of quantity on hand × current variant selling price." },
      { name: "Low / out of stock", formula: "Low: 0 < available ≤ reorder level. Out: available ≤ 0. Values count matching inventory records." },
      { name: "Movement count", formula: "Count of append-only stock movement records in the selected period." },
      { name: "On-hand change", formula: "Sum of quantity-on-hand changes from movements in the selected period." },
    ],
  },
  {
    id: "payments",
    title: "Payments report",
    scope: "Combines online Payment records and POS Payment Entry records in permitted branches. Successful entries use their paid/created date; refunds and cancellations use the correction date. Date boundaries are inclusive local calendar dates.",
    metrics: [
      { name: "Payment entries", formula: "Count of all payment attempts matching the filters." },
      { name: "Successful / pending / refunded", formula: "Count of matching payment entries in the named normalized status." },
      { name: "Failed / cancelled", formula: "Failed payment-entry count + cancelled payment-entry count." },
      { name: "Gross collected", formula: "Sum of successful amounts plus the original collected amounts represented by subsequently refunded entries." },
      { name: "Refunded amount", formula: "Sum of amounts on refunded payment entries." },
      { name: "Net collected", formula: "Gross collected − refunded amount." },
      { name: "Method attempted count", formula: "Count of all entries for the payment method." },
      { name: "Method collected amount", formula: "Sum of successful amounts plus the original collected amounts represented by refunded entries for the method." },
      { name: "Method net collected", formula: "Method collected amount − method refunded amount." },
    ],
  },
  {
    id: "branches",
    title: "Branch comparison report",
    scope: "Applies the same date period and permission scope to each branch; current stock values are point-in-time rather than period totals.",
    metrics: [
      { name: "Branches shown", formula: "Count of permitted branches represented after filters." },
      { name: "Total sales", formula: "Sum of qualifying online-order revenue + completed POS-sale revenue across shown branches." },
      { name: "Sales share", formula: "Branch total sales ÷ combined shown-branch sales × 100; 0% when combined sales are zero." },
      { name: "Bookings / booking value", formula: "Count of matching bookings / sum of their snapshotted service-item prices." },
      { name: "Cancellation / no-show rate", formula: "Branch outcome count ÷ branch booking count × 100; 0% when booking count is zero." },
      { name: "Product revenue / gross profit", formula: "Product line totals / product revenue − sale-time product costs." },
      { name: "Service revenue", formula: "Recognized paid booking-service revenue + completed POS service revenue." },
      { name: "Estimated operating result", formula: "Product gross profit + recognized service revenue. This is an estimate, not net profit: service consumables, labour, commissions, delivery costs, rent, utilities, taxes, and other operating expenses are not yet deducted." },
      { name: "Payments collected", formula: "Successful online Payment amounts + successful POS Payment Entry amounts." },
      { name: "Available stock", formula: "Current quantity on hand − quantity reserved, summed for the branch." },
      { name: "Low / out-of-stock records", formula: "Count of branch inventory records meeting the standard low/out stock definitions." },
    ],
  },
];
