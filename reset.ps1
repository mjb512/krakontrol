Function resetDevice($id)
{
    Disable-PnpDevice -InstanceId $id -Confirm:$false
    Enable-PnpDevice -InstanceId $id -Confirm:$false
}
