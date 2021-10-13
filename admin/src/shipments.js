import React from 'react';
import {
  Switch,
  Route,
  Link,
  useRouteMatch
} from "react-router-dom";


export function ShipmentPage(props) {
	let { url } = useRouteMatch();

	return (
		<Switch>
			<Route path={`${url}/add/`} render={({ match, history }) => <AddShipment listing={props.listing} match={match} parentUrl={url} history={history} />} />
			<Route path={`${url}/edit/:shipmentId`} render={({ match, history }) => <AddShipment listing={props.listing} match={match} parentUrl={url} history={history} />} />
			<Route path={url}>
				<Shipments listing={props.listing} url={url} />
			</Route>
		</Switch>
	);
}

class AddShipment extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			items: null,
			changed: false,
			date: (new Date()).toISOString().substr(0,10),
			time: (new Date()).toISOString().substr(11,8),
			amount: 0,
			comment: "",
			shipment: null
		}
		this.reload  = this.reload.bind(this);
		this.handleItemMemberChange = this.handleItemMemberChange.bind(this);
		this.handleItemChange = this.handleItemChange.bind(this);
		this.handleInputChange = this.handleInputChange.bind(this);
		this.handleClick       = this.handleClick.bind(this);
	}

	handleClick(event) {
		console.log(event);
		let submission = {
			time: this.state.date + "T" + this.state.time,
			amount: this.state.amount,
			comment: this.state.comment,
		}
		submission.items = this.state.items.map((value, key) => ({
				id: value.id, 
				quantity: parseInt(value.shipment_quantity),
				members: value.members.map((v, k) => ({
					id: v.id,
					quantity: parseInt(v.shipment_quantity)
			}))
		}));

		console.log(submission);
		let self = this;

		if (this.state.shipment === null) {
			fetch("/api/listing/" + this.props.listing.id + "/shipments", {method: "POST", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify(submission)})
				.then(
						(results) => self.props.history.push(self.props.parentUrl + window.location.search)
				);
		} else {
			fetch("/api/listing/" + this.props.listing.id + "/shipments/" + this.props.match.params.shipmentId, {method: "PUT", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}, body: JSON.stringify(submission)})
				.then(
						(results) => self.props.history.push(self.props.parentUrl + window.location.search)
				);

		}

		event.stopPropagation();
		event.preventDefault();
	}

	handleInputChange(event) {
		this.setState({[event.target.name]: event.target.value, changed: true});
	}

	reload() {
		const self = this;
		fetch("/api/listing/" + this.props.listing.id + "/shipments" + (this.props.match.params.shipmentId ? ("/" + this.props.match.params.shipmentId) : "") , {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => {
					if (results.shipment !== null) {
						results.amount  = results.shipment.total_cost;
						results.comment = results.shipment.comment;
						results.date = new Date(results.shipment.arrival).toISOString().substr(0,10);
						results.time = new Date(results.shipment.arrival).toISOString().substr(11,8);
					}
					console.log("Writing state", results);
					self.setState(results);
				}
			);
	}

	handleItemMemberChange(event, vendorIndex, memberIndex, min, max) {
		let value = parseInt(event.target.value);
		console.log("Proposed value", value);
		if (isNaN(value) || (value < min))
			value = min;
		else if (value > max)
			value = max;
		console.log("New value", value);

		let items = JSON.parse(JSON.stringify(this.state.items));
		items[vendorIndex].members[memberIndex].shipment_quantity = value;
		this.setState({items: items, changed: true});
		event.stopPropagation();
		event.preventDefault();
	}

	handleItemChange(event, vendorIndex, min, max) {
		let value = parseInt(event.target.value);
		console.log("Proposed value", value);
		if (isNaN(value) || value < min)
			value = min;
		else if (value > max)
			value = max;
		console.log("New value", value);
		let items = JSON.parse(JSON.stringify(this.state.items));
		items[vendorIndex].shipment_quantity = value;
		this.setState({items: items, changed: true});
		event.stopPropagation();
		event.preventDefault();
	}

	componentDidMount() {
		this.reload();
	}

	render() {
		if (this.state.items === null)
			return "";

		const item_rows = this.state.items.map((value, key) => <ShipmentItemEntry currency={this.props.listing.currency} key={value.id} entry={value} index={key} handleItemChange={this.handleItemChange} handleItemMemberChange={this.handleItemMemberChange} />);

		return (<div>
			<h3>Skrá sendingu</h3>
			<form>
				<div className="form-group row">
					<label htmlFor="arrival" className="col-sm-2 col-form-label">Komutími</label>
					<div className="col-sm-4">
						<input type="date"  className="form-control" id="arrival" value={this.state.date} name="date" onChange={this.handleInputChange}/>
					</div>
					<div className="col-sm-4">
						<input type="time"  className="form-control" id="arrival" value={this.state.time} name="time" onChange={this.handleInputChange} />
					</div>
				</div>
				<div className="form-group row">
					<label htmlFor="cost" className="col-sm-2 col-form-label">Samtals kostnaður</label>
					<div className="col-sm-4">
						<input type="number" className="form-control" id="cost" name="amount" value={this.state.amount} onChange={this.handleInputChange}/>
					</div>
					<div className="col-sm-2"><p className="my-1">ISK</p></div>
				</div>
				<div className="form-group row">
					<label htmlFor="comment" className="col-sm-2 col-form-label">Athugasemdir</label>
					<div className="col-sm-8">
						<textarea className="form-control" id="comment" rows="3" name="comment" onChange={this.handleInputChange} value={this.state.comment}></textarea>
					</div>
				</div>

				<table className="table table-sm shipment-order">
					<thead>
						<tr>
							<th key="vendor_id">#</th>
							<th key="name">Hlutur / Meðlimur</th>
							<th key="qty">Magn ókomið</th>
							<th key="received">Magn í sendingu / Magn úthlutað</th>
						</tr>
					</thead>
					{item_rows}
				</table>

				<button type="submit" className="btn btn-primary" disabled={!this.state.changed} onClick={this.handleClick}>Vista</button>
			</form>
		</div>);
	}
}


function ShipmentItemMemberEntry(props) {
	let max = Math.min(props.max, props.entry.remaining_quantity);
	return (<tr className="table-secondary">
		<td></td>
		<td>{props.entry.name} &lt;{props.entry.email}&gt;</td>
		<td>{props.entry.remaining_quantity}</td>
			<td key="received">
				<input type="number" className="form-control" value={props.entry.shipment_quantity} min={0} max={max} onChange={(e) => props.handleItemMemberChange(e, props.itemIndex, props.memberIndex, 0, max)} />
			</td>
		</tr>);

}

function ShipmentItemEntry(props) {
	const min_sum  = props.entry.members.map((value, key) => value.shipment_quantity).reduce((acc, x) => acc + x, 0);
	const leftover = props.entry.shipment_quantity - min_sum;
	if (min_sum > 0) 
		console.log("min_sum", min_sum, "leftover", leftover);
	const members = props.entry.members.map((value, key) => <ShipmentItemMemberEntry key={value.id} entry={value} itemId={props.entry.id} vendorId={props.entry.vendor_id} handleItemMemberChange={props.handleItemMemberChange} itemIndex={props.index} memberIndex={key} max={value.shipment_quantity+leftover} />);
	let cls = "table-primary";

	if (leftover > 0) 
		cls = "table-danger"
	else if (props.entry.missing_quantity > props.entry.shipment_quantity)
		cls = "table-warning"

	return (
		<tbody>
			<tr className={cls}>
				<td key="vendor_id">{props.entry.vendor_id}</td>
				<td key="name"><a href={props.entry.url}>{props.entry.item_name}</a></td>
				<td key="qty">{props.entry.missing_quantity}</td>
				<td key="received">
					<input type="number" className="form-control" value={props.entry.shipment_quantity} min={min_sum} max={props.entry.missing_quantity} onChange={(e) => props.handleItemChange(e, props.index, min_sum, props.entry.missing_quantity)} />
				</td>
			</tr>
			{members}
		</tbody>
	);
}

function ShipmentRow(props) {
	return <tr>
		<td key="arrival">{props.entry.arrival}</td>
		<td key="comments">{props.entry.comment}</td>
		<td key="cost">{props.entry.total_cost.toLocaleString()} kr</td>
		<td key="allocation">{props.entry.allocated_quantity}</td>
		<td key="quantity">{props.entry.delivered_quantity}</td>
		<td key="actions">
			<Link className="btn btn-warning btn-sm mr-2" to={{pathname: `${props.url}/edit/${props.entry.id}`, search: window.location.search}}>Breyta</Link>
			<button onClick={(e) => props.handleDelete(e, props.entry.id)} className="btn btn-danger btn-sm">Eyða</button>
		</td>
	</tr>;
}

class Shipments extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			auth_token: "Bearer " + new URLSearchParams(window.location.search).get("token"),
			shipments: null, 
			order: null,
		};
		this.reload  = this.reload.bind(this);
		this.handleDelete  = this.handleDelete.bind(this);
	}

	reload() {
		fetch("/api/listing/" + this.props.listing.id + "/shipments", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.setState(results)
			);
		fetch("/api/listing/" + this.props.listing.id + "/order", {headers: {'Authorization': this.state.auth_token}})
			.then(res => res.json())
			.then(
				(results) => this.setState(results)
			);
	}

	handleDelete(event, id) { 
		if (window.confirm("Viltu örugglega eyða sendingu?")) {
			fetch("/api/listing/" + this.props.listing.id + "/shipments/" + id, {method: "DELETE", headers: {'Authorization': this.state.auth_token, 'Content-Type': 'application/json'}})
				.then(
						(results) => this.reload()
				);
		}
	}

	componentDidMount() {
		this.reload();
	}

	render() {
		if (this.state.shipments === null || this.state.order === null)
			return "";

		let total_order_qty = this.state.order.reduce((acc, x) => acc + x.qty, 0);
		let rows = this.state.shipments.map((val, idx) => <ShipmentRow key={val.id} entry={val} url={this.props.url} handleDelete={this.handleDelete} />);
		let total_qty  = this.state.shipments.reduce((acc, x) => acc + x.delivered_quantity, 0);
		let total_cost = this.state.shipments.reduce((acc, x) => acc + x.total_cost, 0);
		
		return (
		<div>
			<h3>Sendingar</h3>
			<table className="table table-striped table-hover table-sm">
				<thead>
					<tr>
						<th key="arrival">Tími</th>
						<th key="comments">Athugasemdir</th>
						<th key="cost">Kostnaður</th>
						<th key="allocation">Úthlutað</th>
						<th key="quantity">Fjöldi hluta</th>
						<th key="actions">Aðgerðir</th>
					</tr>
				</thead>
				<tbody>{rows}</tbody>
				<tfoot>
					<tr>
						<th key="heading" colSpan="2">Samtals í sendingum</th>
						<th key="cost">{total_cost.toLocaleString()}</th>
						<th key="allocation"></th>
						<th key="quantity">{total_qty}</th>
						<th key="actions"></th>
					</tr>
					<tr>
						<th key="heading" colSpan="4">Samtals í pöntun</th>
						<th key="quantity">{total_order_qty}</th>
						<th key="actions"></th>
					</tr>
				</tfoot>
			</table>
			<Link className="btn mx-1 btn-primary" to={{pathname: `${this.props.url}/add`, search: window.location.search}}>Skrá nýja pöntun</Link>

			<ul>
				<li>Skrá nýja sendingu - listi yfir hluti sem voru pantaðir og magn hvers hlutar í sendingu</li>
				<li>Úthluta hlutum á einstaklinga</li>
				<li>Senda tölvupósta á alla með lista yfir hluti sem þeir fengu, hvað þeir skulda, hvar þeir geta millifært og hvar þeir geta sótt hlutina.</li>
			</ul>
		</div>);
	}	
}
