#!/usr/bin/env python3
"""
Simple Demo of Dynamic Pricing Engine
Shows real business impact without requiring full infrastructure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from ml.pricing_optimizer import DynamicPricingEngine, ProductFeatures, OptimizationObjective
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich import print as rprint
import time

console = Console()

def demo_executive_summary():
    """Show executive summary of impact"""
    console.print("\n[bold magenta]Dynamic Pricing Engine - Executive Demo[/bold magenta]")
    console.print("=" * 60)
    
    # Monthly metrics
    metrics = {
        "Total Revenue This Month": "$1,127,000",
        "Revenue from Price Optimization": "$127,000",
        "Revenue Increase": "+12.7%",
        "Price Changes Applied": "1,247",
        "Products Optimized": "312 of 470",
        "A/B Tests Completed": "5",
        "Average Margin Improvement": "+2.1pp"
    }
    
    table = Table(title="📊 This Month's Performance", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold green")
    
    for metric, value in metrics.items():
        table.add_row(metric, value)
    
    console.print(table)
    
    # Key wins
    console.print("\n[bold]🏆 Key Wins:[/bold]")
    wins = [
        ("Gaming Headset", "-$10 price", "+$5,200/mo revenue"),
        ("iPhone 15 Case", "+$5 price", "+$3,100/mo revenue"),
        ("HDMI Cable", "Match Amazon", "+$2,800/mo revenue")
    ]
    
    for product, action, impact in wins:
        console.print(f"  • {product}: {action} → [green]{impact}[/green]")

def demo_live_optimization():
    """Demonstrate live price optimization"""
    console.print("\n\n[bold cyan]Live Price Optimization Demo[/bold cyan]")
    console.print("-" * 60)
    
    engine = DynamicPricingEngine()
    
    # Sample products to optimize
    products = [
        {
            "name": "Premium Wireless Headphones",
            "current_price": 279.99,
            "cost": 140.00,
            "competitor_avg": 249.99,
            "elasticity": -0.8
        },
        {
            "name": "Gaming Mouse RGB",
            "current_price": 79.99,
            "cost": 35.00,
            "competitor_avg": 69.99,
            "elasticity": -1.8
        },
        {
            "name": "USB-C Hub 7-in-1",
            "current_price": 49.99,
            "cost": 18.00,
            "competitor_avg": 44.99,
            "elasticity": -3.2
        }
    ]
    
    results = []
    
    console.print("\n🔄 Analyzing products...")
    for product in track(products, description="Optimizing..."):
        time.sleep(0.5)  # Simulate processing
        
        # Create product features
        features = ProductFeatures(
            product_id=f"PROD-{products.index(product)}",
            current_price=product["current_price"],
            cost=product["cost"],
            min_price=product["cost"] * 1.2,
            max_price=product["current_price"] * 1.3,
            stock_quantity=100,
            stock_velocity=5.0,
            elasticity=product["elasticity"],
            competitor_avg_price=product["competitor_avg"],
            competitor_min_price=product["competitor_avg"] * 0.95,
            market_position=product["current_price"] / product["competitor_avg"],
            days_since_last_change=10,
            category="Electronics",
            seasonality_factor=1.0,
            conversion_rate=0.03,
            return_rate=0.05
        )
        
        # Optimize
        result = engine.calculate_optimal_price(features, OptimizationObjective.BALANCED)
        
        results.append({
            "name": product["name"],
            "current": product["current_price"],
            "optimal": result.optimal_price,
            "revenue_impact": result.expected_revenue_change,
            "margin": ((result.optimal_price - product["cost"]) / result.optimal_price * 100)
        })
    
    # Display results
    table = Table(title="💡 Optimization Results")
    table.add_column("Product", style="cyan")
    table.add_column("Current Price", style="yellow")
    table.add_column("Optimal Price", style="green")
    table.add_column("Revenue Impact", style="magenta")
    table.add_column("Margin", style="blue")
    
    total_impact = 0
    for r in results:
        table.add_row(
            r["name"],
            f"${r['current']:.2f}",
            f"${r['optimal']:.2f}",
            f"{r['revenue_impact']:+.1f}%",
            f"{r['margin']:.1f}%"
        )
        total_impact += r['revenue_impact']
    
    console.print("\n")
    console.print(table)
    
    avg_impact = total_impact / len(results)
    console.print(f"\n[bold green]Average Revenue Impact: {avg_impact:+.1f}%[/bold green]")

def demo_competitive_intelligence():
    """Show competitive analysis"""
    console.print("\n\n[bold yellow]Competitive Intelligence[/bold yellow]")
    console.print("-" * 60)
    
    # Competitor comparison
    competitors = {
        "Our Price": 39.99,
        "Amazon": 34.99,
        "BestBuy": 42.99,
        "Walmart": 36.99,
        "Newegg": 35.99
    }
    
    table = Table(title="iPhone 15 Pro Case - Market Analysis")
    table.add_column("Retailer", style="cyan")
    table.add_column("Price", style="yellow")
    table.add_column("vs. Our Price", style="magenta")
    table.add_column("Status", style="green")
    
    our_price = competitors["Our Price"]
    for retailer, price in competitors.items():
        if retailer == "Our Price":
            table.add_row(retailer, f"${price:.2f}", "-", "Current")
        else:
            diff = ((our_price - price) / price * 100)
            status = "In Stock" if retailer != "Walmart" else "Out of Stock"
            table.add_row(
                retailer, 
                f"${price:.2f}", 
                f"{diff:+.1f}%",
                f"[{'green' if status == 'In Stock' else 'red'}]{status}[/]"
            )
    
    console.print(table)
    
    # Opportunity alert
    panel = Panel(
        "[bold]🎯 Opportunity Detected![/bold]\n\n"
        "Walmart is out of stock on this item.\n"
        "Recommendation: Increase price by 5-8% for next 48 hours.\n"
        "Expected additional revenue: [green]+$2,400[/green]",
        title="Price Optimization Alert",
        border_style="green"
    )
    console.print("\n")
    console.print(panel)

def demo_ab_test_results():
    """Show A/B test results"""
    console.print("\n\n[bold blue]A/B Testing Results[/bold blue]")
    console.print("-" * 60)
    
    # Test results
    test = {
        "name": "Gaming Mouse Holiday Pricing",
        "control_price": 129.99,
        "variant_price": 109.99,
        "control_conversions": 45,
        "variant_conversions": 68,
        "control_revenue": 5849.55,
        "variant_revenue": 7479.32,
        "duration": "7 days",
        "confidence": 95
    }
    
    table = Table(title="🧪 Experiment: " + test["name"])
    table.add_column("Metric", style="cyan")
    table.add_column("Control ($129.99)", style="yellow")
    table.add_column("Variant ($109.99)", style="green")
    table.add_column("Lift", style="magenta")
    
    # Calculate metrics
    control_cr = test["control_conversions"] / 2000  # Assuming 2000 visitors
    variant_cr = test["variant_conversions"] / 2000
    cr_lift = ((variant_cr - control_cr) / control_cr * 100)
    
    revenue_lift = ((test["variant_revenue"] - test["control_revenue"]) / test["control_revenue"] * 100)
    
    table.add_row("Price", f"${test['control_price']}", f"${test['variant_price']}", "-15.4%")
    table.add_row("Conversions", str(test["control_conversions"]), str(test["variant_conversions"]), f"+{(test['variant_conversions'] - test['control_conversions']) / test['control_conversions'] * 100:.1f}%")
    table.add_row("Revenue", f"${test['control_revenue']:,.2f}", f"${test['variant_revenue']:,.2f}", f"+{revenue_lift:.1f}%")
    table.add_row("Conversion Rate", f"{control_cr:.1%}", f"{variant_cr:.1%}", f"+{cr_lift:.1f}%")
    
    console.print(table)
    
    # Recommendation
    console.print(f"\n[bold]Statistical Confidence: {test['confidence']}%[/bold]")
    console.print("[bold green]✅ Recommendation: Adopt variant pricing[/bold]")
    console.print(f"Projected annual impact: [green]+${revenue_lift * 12 * 10000 / 100:,.0f}[/green]")

def demo_roi_calculator():
    """Show ROI calculation"""
    console.print("\n\n[bold green]ROI Calculator[/bold green]")
    console.print("-" * 60)
    
    # Business inputs
    annual_revenue = 10_000_000
    num_skus = 500
    avg_order_value = 75
    
    # Impact scenarios
    scenarios = [
        ("Conservative", 0.05, "green"),
        ("Moderate", 0.10, "yellow"),
        ("Aggressive", 0.15, "red")
    ]
    
    table = Table(title="💰 Revenue Impact Projections")
    table.add_column("Scenario", style="cyan")
    table.add_column("Improvement", style="white")
    table.add_column("Monthly Impact", style="green")
    table.add_column("Annual Impact", style="bold green")
    table.add_column("ROI", style="magenta")
    
    for name, improvement, color in scenarios:
        monthly = annual_revenue / 12 * improvement
        annual = annual_revenue * improvement
        roi = (annual / 50000 - 1) * 100  # Assuming $50k investment
        
        table.add_row(
            f"[{color}]{name}[/{color}]",
            f"{improvement:.0%}",
            f"${monthly:,.0f}",
            f"${annual:,.0f}",
            f"{roi:.0f}%"
        )
    
    console.print(table)
    
    # Summary
    console.print("\n[bold]Investment Requirements:[/bold]")
    console.print("  • Software License: $25,000/year")
    console.print("  • Implementation: $15,000 (one-time)")
    console.print("  • Training: $10,000")
    console.print("  • [bold]Total First Year: $50,000[/bold]")
    
    console.print("\n[bold green]Payback Period: 2-4 months[/bold green]")

def main():
    """Run the complete demo"""
    console.clear()
    
    # Header
    console.print(Panel(
        "[bold cyan]Dynamic Pricing Engine[/bold cyan]\n"
        "[italic]Turn static prices into revenue-generating algorithms[/italic]",
        title="💰 Welcome",
        border_style="cyan"
    ))
    
    # Run demo sections
    demo_executive_summary()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_live_optimization()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_competitive_intelligence()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_ab_test_results()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_roi_calculator()
    
    # Footer
    console.print("\n" + "=" * 60)
    console.print(Panel(
        "[bold green]Demo Complete![/bold green]\n\n"
        "The Dynamic Pricing Engine can start optimizing your prices today.\n"
        "Expected impact: [bold]+10-15% revenue increase[/bold]\n\n"
        "[cyan]Contact: sales@dynamicpricing.io[/cyan]",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")