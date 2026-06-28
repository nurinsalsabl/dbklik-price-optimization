const API = "http://127.0.0.1:8000";

let profitChart = null;

function formatRupiah(value){


return new Intl.NumberFormat(
    "id-ID",
    {
        style:"currency",
        currency:"IDR",
        maximumFractionDigits:0
    }
).format(value);


}

async function loadDashboard(){

const res =
    await fetch(
        `${API}/dashboard`
    );

const data =
    await res.json();

document.getElementById(
    "totalProduk"
).innerText =
    data.total_produk;

document.getElementById(
    "totalOmset"
).innerText =
    formatRupiah(
        data.total_omset
    );

document.getElementById(
    "totalProfit"
).innerText =
    formatRupiah(
        data.total_profit
    );

document.getElementById(
    "totalKompetitor"
).innerText =
    data.total_kompetitor;


}

async function loadProducts(){

const res =
    await fetch(
        `${API}/products`
    );

const products =
    await res.json();

const select =
    document.getElementById(
        "productSelect"
    );

select.innerHTML = "";

products.forEach(product => {

    const option =
        document.createElement(
            "option"
        );

    option.value = product;

    option.textContent =
        product;

    select.appendChild(
        option
    );

});


}

async function loadProduct(){

const productName =
    document.getElementById(
        "productSelect"
    ).value;

const res =
    await fetch(
        `${API}/product/${encodeURIComponent(productName)}`
    );

const data =
    await res.json();

document.getElementById(
    "productInfo"
).innerHTML = `

<div class="product-card">

    <h5>
        ${data.Nama_Produk}
    </h5>

    <p>
        Brand :
        ${data.Brand}
    </p>

    <p>
        Harga :
        ${formatRupiah(data.Harga)}
    </p>

    <p>
        HPP :
        ${formatRupiah(data.HPP)}
    </p>

    <p>
        Qty :
        ${data.Qty}
    </p>

    <p>
        Margin :
        ${data.Margin.toFixed(2)}%
    </p>

    <p>
        Kompetitor :
        ${data.Kompetitor}
    </p>

</div>

`;


}

async function simulatePrice(){

const product_name =
    document.getElementById(
        "productSelect"
    ).value;

const new_price = Number(
    document.getElementById("newPrice").value
);

if (!new_price || new_price <= 0) {
    alert("Masukkan harga baru terlebih dahulu.");
    return;

}

const res =
    await fetch(
        `${API}/simulate`,
        {
            method:"POST",

            headers:{
                "Content-Type":
                "application/json"
            },

            body:JSON.stringify({

                product_name,
                new_price

            })

        }
    );

const data =
    await res.json();

document.getElementById(
    "qtyResult"
).innerText =
    data.predicted_qty;

document.getElementById(
    "revenueResult"
).innerText =
    formatRupiah(
        data.predicted_revenue
    );

document.getElementById(
    "profitResult"
).innerText =
    formatRupiah(
        data.predicted_profit
    );

document.getElementById(
    "marginResult"
).innerText =
    data.predicted_margin_pct +
    "%";


}

function drawChart(curve){


const labels =
    curve.map(
        item =>
        Math.round(
            item.price
        )
    );

const profits =
    curve.map(
        item =>
        item.profit
    );

const ctx =
    document.getElementById(
        "profitChart"
    );

if(profitChart){

    profitChart.destroy();

}

profitChart =
    new Chart(ctx,{

        type:"line",

        data:{

            labels:labels,

            datasets:[{

                label:
                "Profit",

                data:profits,

                borderWidth:3

            }]

        }

    });


}

async function optimizePrice(){

const product_name =
    document.getElementById(
        "productSelect"
    ).value;

const res =
    await fetch(
        `${API}/optimize`,
        {
            method:"POST",

            headers:{
                "Content-Type":
                "application/json"
            },

            body:JSON.stringify({

                product_name

            })

        }
    );

const data = await res.json();

console.log(data);

document.getElementById("optimizeResult").innerHTML = `
<h1 style="color:red">BERHASIL MASUK JS</h1>
`;

document.getElementById("optimizeResult").innerHTML = `

<div class="alert alert-success">

    <h4>
        Harga Optimal
    </h4>

    <h2>
        ${formatRupiah(
            data.optimal_price
        )}
    </h2>

    <hr>

    <p>
        Profit Saat Ini :
        ${formatRupiah(
            data.current_profit
        )}
    </p>

    <p>
        Profit Optimal :
        ${formatRupiah(
            data.optimal_profit
        )}
    </p>

    <p>
        Profit Improvement :
        <b>
        ${formatRupiah(
            data.profit_improvement
        )}
        </b>
    </p>
</div>
`;

drawChart(data.curve);
}

window.onload = async () => {
await loadDashboard();
await loadProducts();
};
